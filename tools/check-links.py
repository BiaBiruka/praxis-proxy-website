#!/usr/bin/env python3
"""Run Linkinator over every generated HTML file in bounded batches."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence


BATCH_SIZE = 40
SKIP_EXTERNAL = r"https?://(?!localhost(?=[:/])|127[.]0[.]0[.]1(?=[:/])).*"
ROOT = Path(__file__).resolve().parents[1]
LINKINATOR = ROOT / "node_modules" / ".bin" / "linkinator"


def batches(paths: Sequence[str], size: int = BATCH_SIZE):
    for start in range(0, len(paths), size):
        yield paths[start : start + size]


def run_batch(destination: Path, paths: Sequence[str]) -> int:
    command = [
        str(LINKINATOR), *paths,
        "--server-root", str(destination),
        "--recurse", "--check-fragments", "--check-css",
        "--timeout", "15000", "--verbosity", "error",
        "--skip", SKIP_EXTERNAL,
    ]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def check(destination: Path) -> int:
    destination = destination.resolve()
    if not destination.is_dir():
        print(f"HTML destination does not exist: {destination}", file=sys.stderr)
        return 2
    if not LINKINATOR.is_file():
        print(f"Linkinator is not installed: {LINKINATOR} (run make init)", file=sys.stderr)
        return 2

    files = sorted(path.relative_to(destination).as_posix()
                   for path in destination.rglob("*.html") if path.is_file())
    if not files:
        print(f"No HTML files found under {destination}", file=sys.stderr)
        return 2

    groups = list(batches(files))
    failed = 0
    for number, paths in enumerate(groups, start=1):
        print(f"Linkinator batch {number}/{len(groups)}: {len(paths)} HTML files", flush=True)
        status = run_batch(destination, paths)
        if status:
            failed += 1
            print(f"Linkinator batch {number}/{len(groups)} failed with status {status}", file=sys.stderr)

    if failed:
        print(f"Link check finished: {failed} of {len(groups)} batches failed.", file=sys.stderr)
        return 1
    print(f"Link check passed: all {len(files)} HTML files were checked in {len(groups)} batches.")
    return 0


def main(arguments: Sequence[str]) -> int:
    if len(arguments) != 1:
        print("Usage: python3 tools/check-links.py HTML_DESTINATION", file=sys.stderr)
        return 2
    return check(Path(arguments[0]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
