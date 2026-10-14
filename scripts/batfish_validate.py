#!/usr/bin/env python3
"""Analyze the generated network snapshot and assert expected reachability.

Positive control: HQ staff HTTPS to the HQ server must succeed.
Security control: HQ guest HTTPS to the HQ server must have no successful path.
The positive control is important; without it, a disconnected/unparsed model could
make the deny test appear to pass for the wrong reason.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import time

from pybatfish.client.session import Session
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9996)
    parser.add_argument("--network-name", default="p3_sme_network")
    parser.add_argument("--snapshot-name", default="candidate")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not args.snapshot_dir.is_dir():
        print(f"Snapshot directory not found: {args.snapshot_dir}", file=sys.stderr)
        return 2

    deadline = time.monotonic() + args.timeout
    last_error = None
    bf = None
    while time.monotonic() < deadline:
        try:
            bf = Session(host=args.host, port=args.port)
            bf.list_networks()
            break
        except Exception as exc:
            last_error = exc
            time.sleep(3)
    if bf is None:
        print(f"Cannot connect to Batfish at {args.host}:{args.port}: {last_error}", file=sys.stderr)
        return 2

    try:
        bf.set_network(args.network_name)
        bf.init_snapshot(str(args.snapshot_dir.resolve()), name=args.snapshot_name, overwrite=True)
        status = bf.q.fileParseStatus().answer().frame()
        print("\nBatfish file parse status:")
        if not status.empty:
            print(status.to_string(index=False))
        else:
            print("WARNING: Batfish returned no parsed files.")
            return 2
        failed = status[status["Status"].astype(str).str.upper().eq("FAILED")]
        if not failed.empty:
            print("ERROR: Batfish failed to parse one or more files.", file=sys.stderr)
            return 2

        issues = bf.q.initIssues().answer().frame()
        if not issues.empty:
            print("\nBatfish initialization issues/warnings (review these; not all warnings mean test failure):")
            print(issues.to_string(index=False, max_rows=50))

        # Positive control: this proves that Batfish models a valid end-to-end path.
        staff_headers = HeaderConstraints(
            srcIps="10.10.10.100",
            dstIps="10.10.20.10",
            ipProtocols="TCP",
            dstPorts="443",
        )
        staff_flow = bf.q.reachability(
            pathConstraints=PathConstraints(startLocation="hq-staff"),
            headers=staff_headers,
            actions="success",
        ).answer().frame()
        if staff_flow.empty:
            print("FAIL: expected HQ Staff HTTPS to HQ server to be reachable, but Batfish found no successful flow.", file=sys.stderr)
            return 1
        print(f"PASS: HQ Staff HTTPS to HQ server is reachable ({len(staff_flow)} successful trace row(s)).")

        # Negative control: a guest must never successfully reach the internal HQ server.
        guest_headers = HeaderConstraints(
            srcIps="10.10.30.100",
            dstIps="10.10.20.10",
            ipProtocols="TCP",
            dstPorts="443",
        )
        guest_flow = bf.q.reachability(
            pathConstraints=PathConstraints(startLocation="hq-guest"),
            headers=guest_headers,
            actions="success",
        ).answer().frame()
        if not guest_flow.empty:
            print("FAIL: guest-to-server reachability exists; the proposed policy violates guest isolation.", file=sys.stderr)
            print(guest_flow.to_string(index=False, max_rows=20), file=sys.stderr)
            return 1
        print("PASS: HQ Guest HTTPS to HQ server has no successful path (guest isolation preserved).")
        print("Batfish policy validation PASSED.")
        return 0
    except Exception as exc:
        print(f"Batfish validation ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
