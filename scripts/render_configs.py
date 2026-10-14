#!/usr/bin/env python3
"""Render IOS-style reference configs from YAML + Jinja2 templates.

CI mode uses synthetic keys. Deployment mode reads real lab-only IPsec secrets
from environment variables and never writes into a tracked directory by default.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from common import ROOT, load_project, wildcard_for_network

CI_KEYS = {
    "P3_IPSEC_PSK_HQ_BR1": "P3_CI_ONLY_NOT_A_REAL_SECRET_HQ_BR1",
    "P3_IPSEC_PSK_HQ_BR2": "P3_CI_ONLY_NOT_A_REAL_SECRET_HQ_BR2",
}


def get_vpn_keys(mode: str) -> dict[str, str]:
    if mode == "ci":
        return CI_KEYS.copy()
    if mode != "deployment":
        raise ValueError(f"Unsupported mode: {mode}")

    values = {}
    for name in CI_KEYS:
        value = os.environ.get(name, "")
        if len(value) < 24 or "CI_ONLY" in value.upper() or "CHANGE_ME" in value.upper():
            raise ValueError(
                f"{name} must be supplied in the environment as a unique lab-only key of at least 24 characters."
            )
        values[name] = value
    if values["P3_IPSEC_PSK_HQ_BR1"] == values["P3_IPSEC_PSK_HQ_BR2"]:
        raise ValueError("Use different pre-shared keys for HQ–Branch 1 and HQ–Branch 2.")
    return values


def enrich_sites(sites):
    for site in sites:
        for tunnel in site.get("tunnels", []):
            tunnel["wildcard_mask"] = wildcard_for_network(tunnel["network"])
            tunnel["network_address"] = tunnel["network"].split("/")[0]
    return sites


def render(mode: str, output: Path) -> None:
    global_data, sites_data = load_project()
    sites = enrich_sites(sites_data["sites"])
    vpn_keys = get_vpn_keys(mode)
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    output.mkdir(parents=True, exist_ok=True)

    context = {
        "vlans": global_data["vlans"],
        "sites": sites,
        "test_server_ip": global_data["project"]["test_server_ip"],
        "simulated_internet_ip": global_data["project"]["simulated_internet_ip"],
        "ospf_process_id": global_data["project"]["ospf_process_id"],
        "vpn_keys": vpn_keys,
    }
    for site in sites:
        for template_name, output_name in (
            ("router.j2", f"{site['router']}.cfg"),
            ("switch.j2", f"{site['switch']}.cfg"),
        ):
            rendered = env.get_template(template_name).render(site=site, **context)
            (output / output_name).write_text(rendered, encoding="utf-8")

    isp = sites_data["isp"]
    rendered_isp = env.get_template("isp.j2").render(isp=isp)
    (output / f"{isp['hostname']}.cfg").write_text(rendered_isp, encoding="utf-8")

    print(f"Rendered 7 reference configs to: {output.resolve()}")
    if mode == "ci":
        print("NOTICE: output uses synthetic CI-only IPsec keys and is not for deployment.")
    else:
        print("NOTICE: local deployment-mode output contains supplied IPsec secrets; keep it out of Git and logs.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ci", "deployment"), default="ci")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "rendered")
    args = parser.parse_args()
    try:
        render(args.mode, args.output if args.output.is_absolute() else ROOT / args.output)
    except Exception as exc:
        print(f"Render FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
