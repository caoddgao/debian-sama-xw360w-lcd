#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHONPATH="$project_dir/src" exec /usr/bin/python3 -m sama_lcd.theme_picker
