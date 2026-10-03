"""
File:   test_contract.py
Brief:  Pin down the runtime behaviour of src/main.py as the contract:
        scene jump loops, empty choices, password state not resetting,
        the menu's return key falling into the invalid branch, and action
        results not being written back to scenes.

INTERACTIVE FICTION
A choice-based interactive fiction game implemented in Python.
"""

import builtins
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from harness import ScriptedInput, load_scenes, run_game
from menu import GameMenu
from utils import next_scene


class TestSceneLoopBack(unittest.TestCase):
    """Scene jumps may loop back to the scene they started from."""

    def test_nap_scene_loops_to_itself(self):
        # "Take another nap" (scene 13, action 1) leads back to scene 13.
        trajectory, _ = run_game(
            load_scenes(), ["1", "2", "1", "1", "1", "4", "1", "0321", "1"])
        self.assertEqual(trajectory, [0, 4, 12, 13, 13, 13, 8, 9, 10])

    def test_invalid_tag_loops_back_to_current_scene(self):
        scenes = load_scenes()
        current = scenes[0]
        real_input = builtins.input
        builtins.input = lambda prompt="": ""
        try:
            with redirect_stdout(io.StringIO()):
                destination = next_scene(scenes, 999, current)
        finally:
            builtins.input = real_input
        self.assertIs(destination, current)


class TestEmptyAndInvalidChoice(unittest.TestCase):
    """Empty and invalid choices are rejected and asked for again."""

    def test_empty_choice_is_reprompted(self):
        trajectory, _ = run_game(load_scenes(), ["", "", "2"])
        self.assertEqual(trajectory, [0, 1])

    def test_invalid_choices_are_reprompted(self):
        trajectory, output = run_game(load_scenes(), ["abc", "99", "-1", "2"])
        self.assertEqual(trajectory, [0, 1])
        self.assertEqual(output.count("Invalid input"), 3)


class TestPasswordStateNotReset(unittest.TestCase):
    """Failing a password jumps to the fail scene and stays there; the
    password is asked again and no state is reset between attempts."""

    def test_repeated_failures_stay_on_fail_scene(self):
        trajectory, _ = run_game(
            load_scenes(),
            ["1", "3", "1", "0000", "1", "1111", "1", "0321", "1"])
        # Wrong PIN at scene 8 -> 11; wrong again at 11 -> still 11 (no reset
        # to scene 8); the correct PIN is still accepted afterwards.
        self.assertEqual(trajectory, [0, 4, 8, 11, 11, 9, 10])

    def test_fail_scene_still_requires_password(self):
        scenes = load_scenes()
        fail_scene = scenes[11]
        action = fail_scene.get_action(0)
        self.assertTrue(action.needs_password())
        self.assertEqual(action.password().fail(), 11)


class TestMenuReturnKey(unittest.TestCase):
    """Inside the menu the in-game menu key (0) is not a way back: it falls
    into the invalid-input branch. Only option 1 (Resume) returns, and it
    returns the exact same scene."""

    def setUp(self):
        self.scenes = load_scenes()
        save_file = os.path.join(tempfile.mkdtemp(), "save.txt")
        self.menu = GameMenu(save_file, self.scenes)

    def _open_menu(self, lines):
        output = io.StringIO()
        real_input = builtins.input
        builtins.input = ScriptedInput(lines)
        try:
            with redirect_stdout(output):
                result = self.menu.open(self.scenes[4])
        finally:
            builtins.input = real_input
        return result, output.getvalue()

    def test_zero_key_hits_invalid_branch(self):
        result, output = self._open_menu(["0", "1"])
        self.assertIn("Invalid input. Choose an integer between 1 and 4", output)
        self.assertIs(result, self.scenes[4])

    def test_resume_returns_same_scene_instance(self):
        result, _ = self._open_menu(["1"])
        self.assertIs(result, self.scenes[4])


class TestActionResultNotWrittenBack(unittest.TestCase):
    """Performing an action never mutates the scene it belongs to; scenes
    are shared instances and look identical on every visit."""

    def test_scene_actions_unchanged_after_transition(self):
        scenes = load_scenes()
        scene = scenes[4]
        actions_before = [scene.get_action(i) for i in range(scene.num_actions())]
        results_before = [action.result() for action in actions_before]

        # Jump scene 4 -> scene 5 ("Go to the desk") and back ("Get up").
        destination = next_scene(scenes, actions_before[0].result(), scene)
        self.assertIs(destination, scenes[5])
        back_action = destination.get_action(destination.num_actions() - 1)
        self.assertIs(next_scene(scenes, back_action.result(), destination), scene)

        # Nothing was written back: same action objects, same order, same results.
        self.assertEqual(scene.num_actions(), len(actions_before))
        for i, action in enumerate(actions_before):
            self.assertIs(scene.get_action(i), action)
            self.assertEqual(scene.get_action(i).result(), results_before[i])

    def test_action_result_is_stable(self):
        scenes = load_scenes()
        action = scenes[0].get_action(0)
        self.assertEqual(action.result(), action.result())


class TestConsecutiveReplay(unittest.TestCase):
    """Replaying the same inputs always produces the same game."""

    INPUTS = ["1", "3", "1", "0321", "1"]

    def test_same_state_two_runs(self):
        scenes = load_scenes()
        self.assertEqual(run_game(scenes, self.INPUTS), run_game(scenes, self.INPUTS))

    def test_fresh_state_matches_reused_state(self):
        fresh = run_game(load_scenes(), self.INPUTS)
        reused = load_scenes()
        run_game(reused, self.INPUTS)
        self.assertEqual(fresh, run_game(reused, self.INPUTS))


if __name__ == "__main__":
    unittest.main()
