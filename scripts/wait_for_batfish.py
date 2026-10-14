#!/usr/bin/env python3
"""Wait for a local or CI Batfish service to accept PyBatfish API calls."""
from __future__ import annotations
import argparse
import time
from pybatfish.client.session import Session


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9996)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            bf = Session(host=args.host, port=args.port)
            bf.list_networks()
            print(f"Batfish responded at {args.host}:{args.port}.")
            return 0
        except Exception as exc:
            last_error = exc
            time.sleep(3)
    print(f"Batfish did not become ready within {args.timeout}s. Last error: {last_error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
