#!/usr/bin/env python3
"""Reject deployment files containing common secret placeholders or CI-only keys."""
from pathlib import Path
import re
import sys

PATTERNS = [
    r"P3_CI_ONLY",
    r"CHANGE_ME",
    r"REPLACE_ME",
    r"<REDACTED>",
    r"<YOUR_.*?>",
    r"__SET_VIA_SECRET_MANAGER__",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_deploy_candidate.py <candidate.cfg>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Candidate does not exist: {path}", file=sys.stderr)
        return 2
    content = path.read_text(encoding="utf-8", errors="replace")
    problems = [pattern for pattern in PATTERNS if re.search(pattern, content, re.IGNORECASE)]
    if problems:
        print(f"Deployment candidate rejected; found placeholders: {', '.join(problems)}", file=sys.stderr)
        return 1
    print("Candidate placeholder scan passed. This check does not prove the configuration is safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
