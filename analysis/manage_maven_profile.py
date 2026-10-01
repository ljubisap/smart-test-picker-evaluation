#!/usr/bin/env python3
"""Install or restore a frozen evaluation profile in a subject POM."""

import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("action", choices=("install", "restore"))
p.add_argument("--pom", type=Path, required=True)
p.add_argument("--fragment", type=Path)
args = p.parse_args()
backup = args.pom.with_suffix(args.pom.suffix + ".stp-eval-original")

if args.action == "install":
    if not args.fragment:
        raise SystemExit("--fragment is required")
    if backup.exists():
        raise SystemExit(f"backup already exists: {backup}")
    original = args.pom.read_text()
    marker = "</profiles>"
    if marker not in original:
        raise SystemExit(f"no {marker} in {args.pom}")
    backup.write_text(original)
    args.pom.write_text(original.replace(marker, args.fragment.read_text() + "\n  " + marker, 1))
else:
    if not backup.exists():
        raise SystemExit(f"no backup: {backup}")
    args.pom.write_text(backup.read_text())
    backup.unlink()
