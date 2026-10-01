#!/usr/bin/env bash
# Launch Park Hopper in the current terminal.
cd "$(dirname "$0")" || exit 1
exec python3 -m hopper "$@"
