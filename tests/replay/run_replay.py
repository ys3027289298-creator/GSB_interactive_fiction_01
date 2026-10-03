#!/usr/bin/env python3
"""
File:   run_replay.py
Brief:  Replay the scripted input files in this directory twice through the
        real game (src/main.py) and verify that each script always reaches
        the same ending with byte-identical output.

Run from the repository root:
    python3 tests/replay/run_replay.py
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
REPLAY_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = {
    "ending_pills.txt": ["THE PILLS"],
    "ending_forest.txt": [
        "THE DOOR", "A BREATH OF FRESH AIR", "A BREATH OF HOT HAIR"],
    "loop_nap.txt": ["A QUICK REST", "THE DOOR", "A BREATH OF HOT HAIR"],
}


def run_script(path):
    with open(path, encoding="utf-8") as file:
        data = file.read()
    env = dict(os.environ, TERM="xterm")
    return subprocess.run(
        [sys.executable, os.path.join("src", "main.py")],
        input=data, capture_output=True, text=True,
        cwd=REPO_ROOT, env=env, timeout=60, check=False)


def main():
    failures = 0
    for name, expected_titles in SCRIPTS.items():
        first = run_script(os.path.join(REPLAY_DIR, name))
        second = run_script(os.path.join(REPLAY_DIR, name))
        problems = []
        if first.returncode != 0:
            problems.append(
                f"game exited with code {first.returncode}: "
                f"{first.stderr.strip()}")
        if first.stdout != second.stdout:
            problems.append("output differs between identical runs")
        if not first.stdout.rstrip().endswith("THE END"):
            problems.append("did not reach an ending (missing 'THE END')")
        for title in expected_titles:
            if title not in first.stdout:
                problems.append(f"missing expected scene {title!r}")
        if problems:
            failures += 1
            print(f"FAIL {name}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"OK   {name} (identical output, ending verified)")

    if failures:
        print(f"{failures} replay script(s) failed")
        return 1
    print("All replay scripts reached deterministic endings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
