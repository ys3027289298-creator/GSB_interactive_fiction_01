# Tests

The game is tested through its real entry point: `python3 src/main.py` run
from the repository root, fed with scripted stdin.

## Run everything

```shell
python3 -m unittest discover -s tests -v
```

- `test_runtime.py` — end-to-end playthroughs: scene jumps and loops, empty
  and invalid choices, password failures without state reset, menu back key
  and save/load, action results written back to the current scene, and
  deterministic replays.
- `test_story_graph.py` — static checks on `data/story.json`: unique tags,
  no dangling targets, every scene reachable from the entry scene (tag 0).
- `test_models.py` — hash/eq contract of the model classes.

## Deterministic ending verification

`inputs/good_ending.txt` is a fixed input script that always reaches the same
ending. Replay it any number of times and confirm the playthrough never
changes:

```shell
tests/verify_determinism.sh                              # 5 runs, good ending
tests/verify_determinism.sh tests/inputs/good_ending_noisy.txt 3
```

`inputs/good_ending_noisy.txt` reaches the identical ending while also
exercising empty/invalid choices, the menu back key and a wrong PIN.
