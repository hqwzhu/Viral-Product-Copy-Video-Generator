#!/usr/bin/env python3
"""Generate deterministic SHA-256 checksum records for release artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import distribution_contract as contract


ROOT = Path(__file__).resolve().parents[1]


def write_checksums(root: Path, relative_paths: list[str], output: Path) -> None:
    lines: list[str] = []
    for name in sorted(relative_paths):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"checksum input is missing: {name}")
        lines.append(f"{contract.sha256_file(path).upper()}  {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output", default="SHA256SUMS")
    args = parser.parse_args()
    write_checksums(ROOT, args.paths, ROOT / args.output)


if __name__ == "__main__":
    main()
