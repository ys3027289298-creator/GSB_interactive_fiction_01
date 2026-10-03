#!/usr/bin/env bash
# Replay a fixed input script several times through the real entry point
# (python3 src/main.py, run from the repo root) and verify that every run
# visits the exact same sequence of scenes, i.e. the ending is deterministic.
#
# Usage: tests/verify_determinism.sh [input_script] [runs]
#   input_script  defaults to tests/inputs/good_ending.txt
#   runs          defaults to 5
set -euo pipefail
cd "$(dirname "$0")/.."

INPUT="${1:-tests/inputs/good_ending.txt}"
RUNS="${2:-5}"

TITLES='^(WAKING UP|THE PILLS|UNDER THE DESK|THE NOTE|THE ROOM|THE DESK|THE WATCH|THE DOOR|A BREATH OF FRESH AIR|A BREATH OF HOT HAIR|THE BED|A QUICK REST|THE BOX|THE END)$'

play() {
    # Strip ANSI escape sequences (clear screen) and prompt prefixes, then
    # keep only scene-title lines: that is the playthrough signature.
    TERM=xterm python3 src/main.py < "$1" 2>/dev/null \
        | sed -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/^\([?>] \)\+//' \
        | grep -E "$TITLES" || true
}

reference="$(play "$INPUT")"
if [[ -z "$reference" ]]; then
    echo "FAIL: no scenes were visited; is '$INPUT' a valid script?" >&2
    exit 1
fi

for run in $(seq 2 "$RUNS"); do
    signature="$(play "$INPUT")"
    if [[ "$signature" != "$reference" ]]; then
        echo "FAIL: run $run diverged from run 1" >&2
        diff <(printf '%s\n' "$reference") <(printf '%s\n' "$signature") >&2 || true
        exit 1
    fi
done

echo "OK: $RUNS identical playthroughs of '$INPUT'"
echo "Scene sequence:"
printf '%s\n' "$reference"
