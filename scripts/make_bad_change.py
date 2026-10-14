#!/usr/bin/env python3
"""Create a disposable bad candidate that permits guest traffic to internal 10/8.

This demonstrates a semantic security failure caught by Batfish. Source files are
not modified; output is copied into a separate directory.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

DENY = " deny ip any 10.0.0.0 0.255.255.255 log"
PERMIT = " permit ip any 10.0.0.0 0.255.255.255"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    src = args.source.resolve()
    out = args.output.resolve()
    if not src.is_dir():
        print(f"Source directory not found: {src}", file=sys.stderr)
        return 2
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    target = out / "HQ-R1.cfg"
    if not target.exists():
        print(f"Expected generated file not found: {target}", file=sys.stderr)
        return 2
    config = target.read_text(encoding="utf-8")
    marker = "ip access-list extended GUEST-IN\n"
    start = config.find(marker)
    if start < 0 or DENY not in config[start:]:
        print("Could not safely locate the GUEST-IN deny line; source format may have changed.", file=sys.stderr)
        return 2
    end = config.find("\n!\n", start)
    if end < 0:
        print("Could not find the end of the GUEST-IN ACL section.", file=sys.stderr)
        return 2
    section = config[start:end]
    if PERMIT in section:
        print("The source already contains the demonstration permit line; refusing to duplicate it.", file=sys.stderr)
        return 2
    # Insert a permissive line before the deny to simulate a dangerous ACL policy change.
    section = section.replace(DENY, PERMIT + "\n" + DENY, 1)
    config = config[:start] + section + config[end:]
    if PERMIT not in config[start:start + len(section)]:
        print("Failed to inject the deliberate bad rule.", file=sys.stderr)
        return 2
    target.write_text(config, encoding="utf-8")
    print(f"Created intentionally unsafe candidate at {out}. Do not deploy it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
