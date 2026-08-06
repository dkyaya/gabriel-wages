#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
echo "Resume from the first volume marked held_for_space in the frozen VOLUME_MANIFEST.csv."
echo "Before any accepted local part is removed, record it in the transferred-volume ledger with confirmed_by_user=true."
echo "Assignment hash: 5ee307c414b5370e16b5533c0285a861c99ea0562fa3796fff3ea9ddae1a8fcd"
echo "Run from the original gabriel-wages repository root:"
echo "python $SCRIPT_DIR/run_rolling_packaging.py"
