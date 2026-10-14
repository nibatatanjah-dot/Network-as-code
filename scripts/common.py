"""Shared file-loading and addressing helpers for the P3 scripts."""
from __future__ import annotations

from ipaddress import ip_interface, ip_network
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    """Load a YAML file with safe_load and return its Python data structure."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_project():
    """Load the authoritative project and site data."""
    global_data = load_yaml(ROOT / "data" / "global.yml")
    sites_data = load_yaml(ROOT / "data" / "sites.yml")
    return global_data, sites_data


def interface_network(address: str, mask: str) -> str:
    """Return normalized network notation from an IPv4 address and netmask."""
    return str(ip_interface(f"{address}/{mask}").network)


def wildcard_for_network(cidr: str) -> str:
    """Return the dotted wildcard mask corresponding to an IPv4 prefix."""
    network = ip_network(cidr, strict=True)
    return str(network.hostmask)
