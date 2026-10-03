"""
File:   harness.py
Brief:  Shared helpers for the test suite. The runtime behaviour of
        src/main.py is the contract these tests pin down.

INTERACTIVE FICTION
A choice-based interactive fiction game implemented in Python.
"""

import builtins
import io
import os
import sys
from contextlib import redirect_stdout

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
STORY_FILE = os.path.join(REPO_ROOT, "data", "story.json")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

os.environ.setdefault("TERM", "xterm")

import main  # noqa: E402
from utils import ask_choice, correct_password, next_scene  # noqa: E402


def load_scenes():
    """Load the real story exactly the way main() does."""
    return main.init_game_data(STORY_FILE)


class ScriptedInput:
    """Replacement for builtins.input returning a fixed list of lines."""

    def __init__(self, lines):
        self._lines = list(lines)

    def __call__(self, prompt=""):
        if not self._lines:
            raise EOFError("scripted input exhausted")
        return self._lines.pop(0)


def run_game(scenes, lines, max_steps=200):
    """Replay main()'s loop (menu branch excluded) with scripted input.

    Params:
        `dict` scenes: map of tag -> GameScene, as built by load_scenes().
        `list` lines: input lines consumed in order by ask_choice/password.
    Return:
        `(list, str)` trajectory of visited scene tags (including the final
        game-over scene) and everything printed to stdout."""
    feeder = ScriptedInput(lines)
    output = io.StringIO()
    trajectory = []
    real_input = builtins.input
    builtins.input = feeder
    try:
        with redirect_stdout(output):
            current = next_scene(scenes, 0, None)
            while True:
                trajectory.append(current.tag())
                if current.is_over():
                    break
                if len(trajectory) > max_steps:
                    raise AssertionError("scene loop did not terminate")
                choice = ask_choice(0, current.num_actions())
                if choice == 0:
                    raise AssertionError(
                        "harness does not drive the menu; use the subprocess replay")
                action = current.get_action(choice - 1)
                new_tag = action.result()
                if action.needs_password():
                    if not correct_password(action.password().string()):
                        new_tag = action.password().fail()
                current = next_scene(scenes, new_tag, current)
    finally:
        builtins.input = real_input
    return trajectory, output.getvalue()
