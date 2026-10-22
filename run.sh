#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"
LD_LIBRARY_PATH="$project_dir/vendor/debian-deps/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
PYTHONPATH="$project_dir/src:$project_dir/vendor/debian-deps/usr/lib/python3/dist-packages" \
  "$project_dir/.venv/bin/python" -m sama_lcd.cli "$@"

