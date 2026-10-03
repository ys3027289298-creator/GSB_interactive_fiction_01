"""
Static checks on data/story.json: every scene must be reachable from the
entry scene (tag 0) and no action may point to a missing scene.

Run with:  python3 -m unittest discover -s tests -v
"""

import json
import unittest
from collections import deque
from pathlib import Path

STORY_FILE = Path(__file__).resolve().parent.parent / "data" / "story.json"


def load_graph():
    """Return (tags, edges) where edges maps a tag to the set of tags its
    actions (and password failures) lead to."""
    with open(STORY_FILE, encoding="UTF-8") as file:
        data = json.load(file)
    tags = set()
    edges = {}
    for obj in data:
        tag = obj["tag"]
        targets = set()
        for action in obj["actions"]:
            targets.add(action["result"])
            if "password" in action:
                targets.add(action["password"]["fail"])
        tags.add(tag)
        edges[tag] = targets
    return tags, edges


class TestStoryGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tags, cls.edges = load_graph()

    def test_entry_scene_exists_and_tags_are_unique(self):
        with open(STORY_FILE, encoding="UTF-8") as file:
            data = json.load(file)
        all_tags = [obj["tag"] for obj in data]
        self.assertEqual(len(all_tags), len(set(all_tags)), "scene tags must be unique")
        self.assertIn(0, self.tags, "the entry scene must have tag 0")

    def test_no_dangling_targets(self):
        for tag, targets in self.edges.items():
            for target in targets:
                self.assertIn(target, self.tags, f"scene {tag} points to missing scene {target}")

    def test_all_scenes_reachable_from_entry(self):
        visited = {0}
        queue = deque([0])
        while queue:
            tag = queue.popleft()
            for target in self.edges.get(tag, ()):
                if target not in visited:
                    visited.add(target)
                    queue.append(target)
        self.assertEqual(visited, self.tags, f"unreachable scenes: {self.tags - visited}")

    def test_game_over_scenes_are_sinks(self):
        with open(STORY_FILE, encoding="UTF-8") as file:
            data = json.load(file)
        for obj in data:
            if obj["gameOver"]:
                self.assertEqual(obj["actions"], [], f"scene {obj['tag']} ends the game")
            else:
                self.assertNotEqual(obj["actions"], [], f"scene {obj['tag']} is a dead end")


if __name__ == "__main__":
    unittest.main()
