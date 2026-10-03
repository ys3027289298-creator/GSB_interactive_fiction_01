"""
File:   test_replay.py
Brief:  End-to-end contract: feed the scripted input files in tests/replay/
        to the real src/main.py process and verify every run reaches the
        same ending with byte-identical output.

INTERACTIVE FICTION
A choice-based interactive fiction game implemented in Python.
"""

import os
import subprocess
import sys
import unittest

from harness import REPO_ROOT

REPLAY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replay")

# Every script is expected to visit these scene titles (in any order) and
# reach an ending.
SCRIPTS = {
    "ending_pills.txt": ["THE PILLS"],
    "ending_forest.txt": [
        "THE DOOR", "A BREATH OF FRESH AIR", "A BREATH OF HOT HAIR"],
    "loop_nap.txt": ["A QUICK REST", "THE DOOR", "A BREATH OF HOT HAIR"],
}


def run_script(name):
    with open(os.path.join(REPLAY_DIR, name), encoding="utf-8") as file:
        data = file.read()
    env = dict(os.environ, TERM="xterm")
    return subprocess.run(
        [sys.executable, os.path.join("src", "main.py")],
        input=data, capture_output=True, text=True,
        cwd=REPO_ROOT, env=env, timeout=60, check=False)


class TestReplayDeterminism(unittest.TestCase):

    def test_replays_are_deterministic(self):
        for name, expected_titles in SCRIPTS.items():
            with self.subTest(script=name):
                first = run_script(name)
                second = run_script(name)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(first.stdout, second.stdout)
                self.assertTrue(first.stdout.rstrip().endswith("THE END"))
                for title in expected_titles:
                    self.assertIn(title, first.stdout)


if __name__ == "__main__":
    unittest.main()
