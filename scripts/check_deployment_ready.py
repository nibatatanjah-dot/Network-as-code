#!/usr/bin/env python3
"""Fail closed unless an explicitly prepared, external/local deployment bundle is safe to attempt.

This is a guardrail, not an authorization system and not a proof that IOS config is correct.
"""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "I_RECONCILED_THIS_CANDIDATE_WITH_THE_LAB_BASELINE"
DEVICES = ["HQ-R1", "BR1-R1", "BR2-R1", "HQ-SW1", "BR1-SW1", "BR2-SW1"]
DOCUMENTATION_NETWORKS = [
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
]


def fail(message: str) -> int:
    print(f"Deployment blocked: {message}", file=sys.stderr)
    return 1


def candidate_dir() -> Path | None:
    raw = os.environ.get("P3_CANDIDATE_DIR", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        return None
    return path.resolve()


def main() -> int:
    if os.environ.get("P3_ENABLE_DEPLOYMENT") != "YES_I_HAVE_A_DISPOSABLE_LAB":
        return fail("set P3_ENABLE_DEPLOYMENT only for a disposable compatible lab.")

    folder = candidate_dir()
    if folder is None:
        return fail("P3_CANDIDATE_DIR must be set to an absolute local path. Keep candidates outside the Git checkout on a self-hosted runner.")
    marker = folder / "DEPLOYMENT_READY"
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != EXPECTED:
        return fail(f"create {marker} with the exact reconciliation phrase after review.")

    inventory_file = ROOT / "inventory" / "hosts.yml"
    try:
        inventory = yaml.safe_load(inventory_file.read_text(encoding="utf-8"))
        host_group = inventory["all"]["children"]["network_devices"]
        group_vars = host_group.get("vars", {})
        hosts = host_group.get("hosts", {})
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        return fail(f"cannot parse {inventory_file}: {exc}")

    missing_hosts = [name for name in DEVICES if name not in hosts]
    if missing_hosts:
        return fail(f"inventory missing required hosts: {', '.join(missing_hosts)}")

    for name in DEVICES:
        host = hosts[name]
        # Require explicit per-host verification so an inherited false/default cannot be mistaken for proof.
        for flag in ("deployment_verified", "p3_rollback_method_verified"):
            if host.get(flag) is not True:
                return fail(f"inventory host {name} must explicitly set {flag}: true after testing it.")
        address = str(host.get("ansible_host", "")).strip()
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return fail(f"inventory host {name} ansible_host must be a real lab management IP; got {address!r}.")
        if any(parsed in net for net in DOCUMENTATION_NETWORKS):
            return fail(f"inventory host {name} still uses documentation TEST-NET address {address}.")

        config = folder / f"{name}.cfg"
        if not config.is_file():
            return fail(f"missing local reviewed candidate for {name}: {config}")

    if group_vars.get("ansible_connection") != "ansible.netcommon.network_cli":
        return fail("inventory must use the expected ansible.netcommon.network_cli connection for IOS.")

    print(f"Pre-flight file/inventory checks passed for six target devices in {folder}.")
    print("This is not a substitute for a human review, console recovery, or a successful rollback drill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
