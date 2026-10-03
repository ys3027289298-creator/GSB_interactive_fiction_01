"""
End-to-end tests driving the game through its real entry point.

Contract: the game is launched as `python3 src/main.py` from the repository
root, exactly as documented in README.md, and is fed a scripted stdin.

Run with:  python3 -m unittest discover -s tests -v
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN = REPO_ROOT / "src" / "main.py"
SAVE_FILE = REPO_ROOT / "data" / "save.txt"
INPUTS = Path(__file__).resolve().parent / "inputs"

# Every scene title in data/story.json, printed upper-cased by GameScene.show().
TITLES = [
    "WAKING UP", "THE PILLS", "UNDER THE DESK", "THE NOTE", "THE ROOM",
    "THE DESK", "THE WATCH", "THE DOOR", "A BREATH OF FRESH AIR",
    "A BREATH OF HOT HAIR", "THE BED", "A QUICK REST", "THE BOX",
]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def run_game(stdin_text):
    """Run one full game with the given stdin script and return the CompletedProcess."""
    env = dict(os.environ, TERM="xterm")
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=30,
    )


def scene_sequence(stdout):
    """Extract the ordered sequence of scene titles (plus THE END) from game output."""
    sequence = []
    for line in ANSI_RE.sub("", stdout).splitlines():
        line = line.strip()
        # The "? " / "> " prompts (possibly several, after empty inputs) get
        # glued to the next scene title because piped stdin is not echoed.
        line = re.sub(r"^(?:\? |> )+", "", line)
        if line in TITLES or line == "THE END":
            sequence.append(line)
    return sequence


class TestSceneJumps(unittest.TestCase):
    """Scene-to-scene jumps, including loops back to already visited scenes."""

    def test_good_ending_path(self):
        result = run_game("1\n3\n1\n0321\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "THE ROOM", "THE DOOR", "A BREATH OF FRESH AIR",
             "A BREATH OF HOT HAIR", "THE END"],
        )

    def test_bad_ending_path(self):
        result = run_game("2\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(scene_sequence(result.stdout), ["WAKING UP", "THE PILLS", "THE END"])

    def test_scene_loop_back_and_forth(self):
        # 0 -> 4 -> 5 -> 4 -> 5 -> 1: jumping back to a visited scene works.
        result = run_game("1\n1\n5\n1\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "THE ROOM", "THE DESK", "THE ROOM", "THE DESK",
             "THE PILLS", "THE END"],
        )


class TestChoiceInput(unittest.TestCase):
    """Empty and out-of-range choices are rejected and re-asked."""

    def test_empty_choice_is_reasked(self):
        result = run_game("\n\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(scene_sequence(result.stdout), ["WAKING UP", "THE PILLS", "THE END"])

    def test_invalid_choice_is_reasked(self):
        result = run_game("abc\n99\n-1\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Invalid input. Choose an integer between 0 and 5", result.stdout)
        self.assertEqual(scene_sequence(result.stdout), ["WAKING UP", "THE PILLS", "THE END"])


class TestPassword(unittest.TestCase):
    """Failing a password lands on the fail scene; state is not reset between tries."""

    def test_wrong_pin_goes_to_fail_scene_then_retry_succeeds(self):
        result = run_game("1\n3\n1\n0000\n1\n0321\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("A loud BEEP"), 1)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "THE ROOM", "THE DOOR", "THE DOOR",
             "A BREATH OF FRESH AIR", "A BREATH OF HOT HAIR", "THE END"],
        )

    def test_multiple_failures_keep_same_state(self):
        # Two wrong PINs in a row: the fail scene is re-entered each time and
        # the door still accepts the correct PIN afterwards (no lockout/reset).
        result = run_game("1\n3\n1\n0000\n1\n1111\n1\n0321\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("A loud BEEP"), 2)
        self.assertIn("A BREATH OF HOT HAIR", scene_sequence(result.stdout))


class TestMenu(unittest.TestCase):
    """Menu access via 0 and the behaviour of its options."""

    def tearDown(self):
        SAVE_FILE.unlink(missing_ok=True)

    def test_menu_back_key_returns_to_same_scene(self):
        # Open the menu, choose Resume (1): the game must come back to the very
        # same scene, not branch elsewhere. Choice 2 afterwards is "Take the
        # pills" of the WAKING UP scene.
        result = run_game("0\n1\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("MENU", result.stdout)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "WAKING UP", "THE PILLS", "THE END"],
        )

    def test_menu_invalid_choice_stays_in_menu(self):
        result = run_game("0\n0\n9\n1\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Invalid input. Choose an integer between 1 and 4", result.stdout)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "WAKING UP", "THE PILLS", "THE END"],
        )

    def test_menu_save_and_load_roundtrip(self):
        # Save at WAKING UP, move on, then load: the game must resume from the
        # saved scene, where choice 2 is "Take the pills".
        result = run_game("0\n2\n\n1\n0\n3\n\n2\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("Done."), 2)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "WAKING UP", "THE ROOM", "WAKING UP", "THE PILLS", "THE END"],
        )


class TestActionResultWriteBack(unittest.TestCase):
    """Performing an action writes its result back: the next scene shown is
    exactly the one the action points to, and the game continues from there."""

    def test_action_result_becomes_current_scene(self):
        # From THE ROOM (tag 4), action 2 is "Go to the bed" (tag 12); the bed
        # scene's own actions must be the ones available next (action 4 there
        # is "Go to the door", tag 8).
        result = run_game("1\n2\n4\n1\n0321\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            scene_sequence(result.stdout),
            ["WAKING UP", "THE ROOM", "THE BED", "THE DOOR",
             "A BREATH OF FRESH AIR", "A BREATH OF HOT HAIR", "THE END"],
        )


class TestReplayDeterminism(unittest.TestCase):
    """Replaying the same input script always yields the same playthrough."""

    def test_repeated_replays_are_identical(self):
        script = (INPUTS / "good_ending.txt").read_text(encoding="UTF-8")
        runs = [run_game(script) for _ in range(3)]
        for result in runs:
            self.assertEqual(result.returncode, 0)
        sequences = [scene_sequence(result.stdout) for result in runs]
        self.assertTrue(all(seq == sequences[0] for seq in sequences))
        self.assertEqual(sequences[0][-1], "THE END")

    def test_noisy_and_clean_scripts_reach_same_ending(self):
        clean = run_game((INPUTS / "good_ending.txt").read_text(encoding="UTF-8"))
        noisy = run_game((INPUTS / "good_ending_noisy.txt").read_text(encoding="UTF-8"))
        self.assertEqual(noisy.returncode, 0)
        # The noisy script detours (menu, wrong PIN) but the ending is identical.
        self.assertEqual(scene_sequence(clean.stdout)[-2:], scene_sequence(noisy.stdout)[-2:])
        self.assertEqual(scene_sequence(noisy.stdout)[-2:], ["A BREATH OF HOT HAIR", "THE END"])


if __name__ == "__main__":
    unittest.main()
