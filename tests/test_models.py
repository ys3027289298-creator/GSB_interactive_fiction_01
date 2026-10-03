"""
Unit tests for the model classes (hash/eq contract used by the game).

Run with:  python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from action import GameAction
from password import GamePassword
from scene import GameScene


class TestHashContract(unittest.TestCase):
    def test_password_is_hashable(self):
        password = GamePassword("0321", 11)
        self.assertEqual(hash(password), hash(GamePassword("0321", 11)))
        self.assertEqual(len({password, GamePassword("0321", 11)}), 1)

    def test_action_is_hashable(self):
        action = GameAction("Enter PIN", 9, GamePassword("0321", 11))
        self.assertEqual(hash(action), hash(GameAction("Enter PIN", 9, None)))
        self.assertIn(action, {GameAction("Enter PIN", 9, None)})

    def test_scene_is_hashable(self):
        scene = GameScene(0, "Title", "Description", True, [])
        self.assertEqual(hash(scene), hash(GameScene(0, "Title", "Description", True, [])))
        self.assertEqual(len({scene, GameScene(0, "Title", "Description", True, [])}), 1)


if __name__ == "__main__":
    unittest.main()
