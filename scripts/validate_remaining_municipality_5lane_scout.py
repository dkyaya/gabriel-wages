#!/usr/bin/env python3
"""Independent entry point for the no-call five-lane queue validator."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import prepare_remaining_municipality_5lane_scout as prep


def main() -> int:
    result = prep.validate(prep.OUTPUT)
    tree = ast.parse(Path(prep.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    prohibited = {"openai", "requests", "httpx", "urllib", "gabriel"}
    if imported & prohibited:
        raise AssertionError(f"prep script imports live/network libraries: {sorted(imported & prohibited)}")
    result["prep_script_live_network_imports"] = 0
    result["live_calls"] = 0
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
