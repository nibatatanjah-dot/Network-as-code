#!/usr/bin/env python3
"""Build an ephemeral pyATS testbed from the Ansible inventory.

The generated testbed contains IP addresses but only environment-variable references
for credentials. It is written below build/ by default, which is ignored by Git.
"""
from __future__ import annotations

import argparse
import ipaddress
from pathlib import Path
import sys
import yaml

from common import ROOT

REQUIRED_DEVICES = {
    "HQ-R1": "router",
    "BR1-R1": "router",
    "BR2-R1": "router",
    "HQ-SW1": "switch",
    "BR1-SW1": "switch",
    "BR2-SW1": "switch",
}
TEST_NETS = [
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
]


def build(inventory_path: Path, output_path: Path) -> None:
    inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    hosts = inventory["all"]["children"]["network_devices"]["hosts"]
    missing = sorted(set(REQUIRED_DEVICES) - set(hosts))
    if missing:
        raise ValueError(f"Inventory is missing pyATS target(s): {', '.join(missing)}")

    devices = {}
    for name, role in REQUIRED_DEVICES.items():
        address = ipaddress.ip_address(str(hosts[name].get("ansible_host", "")))
        if any(address in net for net in TEST_NETS):
            raise ValueError(f"{name} still has a documentation TEST-NET address ({address}); replace inventory first.")
        devices[name] = {
            "os": "ios",
            "type": role,
            "connections": {
                "cli": {
                    "protocol": "ssh",
                    "ip": str(address),
                    "port": 22,
                    "arguments": {"connection_timeout": 30},
                }
            },
        }

    testbed = {
        "testbed": {
            "name": "P3-SME-SSH-Lab",
            "credentials": {
                "default": {
                    "username": "%ENV{P3_DEVICE_USERNAME}",
                    "password": "%ENV{P3_DEVICE_PASSWORD}",
                },
                "enable": {"password": "%ENV{P3_ENABLE_PASSWORD}"},
            },
        },
        "devices": devices,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(testbed, sort_keys=False), encoding="utf-8")
    print(f"Built temporary pyATS testbed for {len(devices)} IOS devices: {output_path.resolve()}")
    print("Credentials remain as %ENV references; set P3_DEVICE_USERNAME/P3_DEVICE_PASSWORD/P3_ENABLE_PASSWORD when running pyATS.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "inventory" / "hosts.yml")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "pyats_testbed.yml")
    args = parser.parse_args()
    inventory_path = args.inventory if args.inventory.is_absolute() else ROOT / args.inventory
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        build(inventory_path, output_path)
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"pyATS testbed generation FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
