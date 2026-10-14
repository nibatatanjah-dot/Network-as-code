#!/usr/bin/env python3
"""Create a Batfish snapshot directory from generated reference configs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
from common import ROOT, load_project


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs", type=Path, default=ROOT / "build" / "rendered")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "batfish_snapshot")
    args = parser.parse_args()
    config_dir = args.configs if args.configs.is_absolute() else ROOT / args.configs
    out_dir = args.output if args.output.is_absolute() else ROOT / args.output
    if not config_dir.is_dir():
        print(f"Config directory does not exist: {config_dir}", file=sys.stderr)
        return 1

    global_data, sites_data = load_project()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "configs").mkdir(parents=True)
    (out_dir / "hosts").mkdir(parents=True)
    config_files = sorted(config_dir.glob("*.cfg"))
    if len(config_files) != 7:
        print(f"Expected seven rendered device configs, found {len(config_files)}.", file=sys.stderr)
        return 1
    for source in config_files:
        shutil.copy2(source, out_dir / "configs" / source.name)

    hosts = []
    for site in sites_data["sites"]:
        hosts.append({
            "hostname": f"{site['key']}-guest",
            "hostInterfaces": {
                "eth0": {
                    "name": "eth0",
                    "prefix": f"{site['test_hosts']['guest']}/24",
                    "gateway": f"10.{site['site_id']}.30.1",
                }
            },
        })
    hq = next(site for site in sites_data["sites"] if site["key"] == "hq")
    hosts.extend([
        {
            "hostname": "hq-staff",
            "hostInterfaces": {
                "eth0": {"name": "eth0", "prefix": f"{hq['test_hosts']['staff']}/24", "gateway": "10.10.10.1"}
            },
        },
        {
            "hostname": "hq-server",
            "hostInterfaces": {
                "eth0": {"name": "eth0", "prefix": f"{global_data['project']['test_server_ip']}/24", "gateway": "10.10.20.1"}
            },
        },
    ])
    for host in hosts:
        path = out_dir / "hosts" / f"{host['hostname']}.json"
        path.write_text(json.dumps(host, indent=2) + "\n", encoding="utf-8")
    print(f"Built Batfish snapshot at {out_dir.resolve()} with {len(config_files)} configs and {len(hosts)} modeled hosts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
