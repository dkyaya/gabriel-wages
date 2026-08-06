#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 PARTS_DIRECTORY DESTINATION" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/extract_all.py" "$1" "$2"
