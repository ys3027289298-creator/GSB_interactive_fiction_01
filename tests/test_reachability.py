"""
File:   test_reachability.py
Brief:  Graph-level checks on the story: every scene is reachable from the
        entry scene (tag 0) and every action target exists.

INTERACTIVE FICTION
A choice-based interactive fiction game implemented in Python.
"""

import unittest

from harness import load_scenes


def targets_of(scene):
    """Collect every tag a scene can jump to (action results + password fails)."""
    targets = []
    for i in range(scene.num_actions()):
        action = scene.get_action(i)
        targets.append(action.result())
        if action.needs_password():
            targets.append(action.password().fail())
    return targets


class TestReachability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scenes = load_scenes()

    def test_entry_scene_exists(self):
        self.assertIn(0, self.scenes)

    def test_all_scenes_reachable_from_entry(self):
        visited = set()
        stack = [0]
        while stack:
            tag = stack.pop()
            if tag in visited:
                continue
            visited.add(tag)
            stack.extend(targets_of(self.scenes[tag]))
        self.assertEqual(visited, set(self.scenes.keys()))

    def test_every_action_target_exists(self):
        for tag, scene in self.scenes.items():
            for target in targets_of(scene):
                self.assertIn(target, self.scenes,
                              f"scene {tag} jumps to missing tag {target}")

    def test_game_over_scenes_are_terminal(self):
        for scene in self.scenes.values():
            if scene.is_over():
                self.assertEqual(scene.num_actions(), 0)
            else:
                self.assertGreater(scene.num_actions(), 0)


if __name__ == "__main__":
    unittest.main()
