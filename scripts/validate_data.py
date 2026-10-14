#!/usr/bin/env python3
"""Validate the P3 YAML source of truth before configuration rendering."""
from __future__ import annotations

import ipaddress
import sys
from pathlib import Path

from common import ROOT, load_project


def validate() -> list[str]:
    errors: list[str] = []
    try:
        global_data, sites_data = load_project()
    except Exception as exc:  # report YAML/path errors with a clean CLI message
        return [f"Could not load YAML source data: {exc}"]

    sites = sites_data.get("sites", [])
    expected_keys = {"hq", "branch1", "branch2"}
    found_keys = {site.get("key") for site in sites}
    if found_keys != expected_keys:
        errors.append(f"Expected exactly site keys {sorted(expected_keys)}, got {sorted(found_keys)}")
    expected_ids = {"hq": 10, "branch1": 20, "branch2": 30}
    for site in sites:
        key = site.get("key")
        if key in expected_ids and site.get("site_id") != expected_ids[key]:
            errors.append(f"{key}: site_id must be {expected_ids[key]} because the address template depends on it.")

    ids = [site.get("site_id") for site in sites]
    if len(ids) != len(set(ids)):
        errors.append("Site IDs must be unique.")

    vlan_ids = [v.get("id") for v in global_data.get("vlans", [])]
    if len(vlan_ids) != len(set(vlan_ids)):
        errors.append("VLAN IDs must be unique.")
    required_vlans = {10, 20, 30, 99, 999}
    if set(vlan_ids) != required_vlans:
        errors.append(f"Expected VLAN IDs {sorted(required_vlans)}.")

    allowed = set(global_data.get("trunk", {}).get("allowed_vlans", []))
    if allowed != {10, 20, 30, 99}:
        errors.append("Trunks must allow VLANs 10, 20, 30 and 99; native VLAN 999 is intentionally not carried.")
    if global_data.get("trunk", {}).get("native_vlan") != 999:
        errors.append("Native/parking VLAN must be 999.")

    wan_networks = []
    router_names = []
    switch_names = []
    router_ids = []
    lan_networks = []
    tunnel_networks = []
    for site in sites:
        key = site.get("key", "<unknown>")
        router_names.append(site.get("router"))
        switch_names.append(site.get("switch"))
        router_ids.append(site.get("router_id"))
        try:
            site_id = int(site["site_id"])
            wan = site["wan"]
            wan_if = ipaddress.ip_interface(f"{wan['address']}/{wan['mask']}")
            wan_net = wan_if.network
            if wan_net.prefixlen != 30:
                errors.append(f"{key}: WAN link must be /30, found {wan_net}.")
            wan_address = ipaddress.ip_address(wan["address"])
            next_hop = ipaddress.ip_address(wan["next_hop"])
            if wan_address not in wan_net or wan_address in (wan_net.network_address, wan_net.broadcast_address):
                errors.append(f"{key}: WAN address {wan_address} is not a usable host in {wan_net}.")
            if next_hop not in wan_net or next_hop in (wan_net.network_address, wan_net.broadcast_address):
                errors.append(f"{key}: WAN next hop {next_hop} is not a usable host in {wan_net}.")
            if wan_address == next_hop:
                errors.append(f"{key}: WAN address and next hop must be different hosts.")
            if wan.get("peer_network") != str(wan_net):
                errors.append(f"{key}: peer_network {wan.get('peer_network')} does not match computed WAN {wan_net}.")
            wan_networks.append((key, wan_net))

            for vlan_id in (10, 20, 30, 99):
                expected = ipaddress.ip_network(f"10.{site_id}.{vlan_id}.0/24")
                gateway = ipaddress.ip_address(f"10.{site_id}.{vlan_id}.1")
                if gateway not in expected:
                    errors.append(f"{key}: gateway {gateway} is not in {expected}.")
                lan_networks.append((f"{key}-VLAN{vlan_id}", expected))

            switch_ip = ipaddress.ip_address(site["switch_management_ip"])
            if switch_ip not in ipaddress.ip_network(f"10.{site_id}.99.0/24"):
                errors.append(f"{key}: switch management IP {switch_ip} is not in its VLAN 99 subnet.")

            expected_tunnels = 2 if key == "hq" else 1
            if len(site.get("tunnels", [])) != expected_tunnels:
                errors.append(f"{key}: expected {expected_tunnels} GRE tunnel definition(s).")
            for tunnel in site.get("tunnels", []):
                ti = ipaddress.ip_interface(f"{tunnel['local_address']}/{tunnel['local_mask']}")
                remote_tunnel_ip = ipaddress.ip_address(tunnel["remote_address"])
                if ti.network.prefixlen != 30:
                    errors.append(f"{key}/{tunnel['interface']}: GRE tunnel must use /30 in this reference model.")
                if ti.network != ipaddress.ip_network(tunnel["network"]):
                    errors.append(f"{key}/{tunnel['interface']}: local tunnel IP and network do not match.")
                if ti.ip in (ti.network.network_address, ti.network.broadcast_address):
                    errors.append(f"{key}/{tunnel['interface']}: local tunnel IP is not usable in {ti.network}.")
                if remote_tunnel_ip not in ti.network or remote_tunnel_ip in (ti.network.network_address, ti.network.broadcast_address):
                    errors.append(f"{key}/{tunnel['interface']}: remote tunnel IP is not a usable host on {ti.network}.")
                if remote_tunnel_ip == ti.ip:
                    errors.append(f"{key}/{tunnel['interface']}: local and remote tunnel IPs must differ.")
                tunnel_networks.append((f"{key}-{tunnel['interface']}", ti.network))
                if tunnel["key_environment_variable"] not in {
                    "P3_IPSEC_PSK_HQ_BR1", "P3_IPSEC_PSK_HQ_BR2"
                }:
                    errors.append(f"{key}/{tunnel['interface']}: unapproved key environment variable name.")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{key}: missing or invalid address/site value: {exc}")

    # Verify that each site WAN next-hop really matches an interface on the modeled ISP.
    isp = sites_data.get("isp", {})
    isp_interfaces = isp.get("interfaces", [])
    isp_by_ip = {}
    for intf in isp_interfaces:
        try:
            address = ipaddress.ip_address(intf["address"])
            intf_network = ipaddress.ip_interface(f"{intf['address']}/{intf['mask']}").network
            if address in (intf_network.network_address, intf_network.broadcast_address):
                errors.append(f"ISP/{intf.get('name')}: interface address {address} is not usable in {intf_network}.")
            isp_by_ip[str(address)] = (intf.get("name"), intf_network)
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"ISP: invalid interface definition {intf}: {exc}")
    for site in sites:
        try:
            wan = site["wan"]
            next_hop = str(ipaddress.ip_address(wan["next_hop"]))
            isp_peer = isp_by_ip.get(next_hop)
            site_network = ipaddress.ip_interface(f"{wan['address']}/{wan['mask']}").network
            if isp_peer is None:
                errors.append(f"{site.get('key')}: WAN next hop {next_hop} is not configured on an ISP interface.")
            elif isp_peer[1] != site_network:
                errors.append(f"{site.get('key')}: WAN subnet {site_network} does not match ISP peer subnet {isp_peer[1]}.")
        except (KeyError, ValueError, TypeError):
            # More precise malformed-value messages were already collected in the main site loop.
            pass

    # Verify that GRE peer definitions point at the partner router's configured WAN and tunnel IP.
    by_router = {site.get("router"): site for site in sites}
    for site in sites:
        for tunnel in site.get("tunnels", []):
            peer_site = by_router.get(tunnel.get("remote_router"))
            if peer_site is None:
                errors.append(f"{site.get('key')}/{tunnel.get('interface')}: unknown remote_router {tunnel.get('remote_router')}.")
                continue
            if tunnel.get("remote_wan_address") != peer_site.get("wan", {}).get("address"):
                errors.append(f"{site.get('key')}/{tunnel.get('interface')}: remote WAN address does not match {peer_site.get('router')} WAN address.")
            matching_peer_tunnel = next(
                (peer for peer in peer_site.get("tunnels", []) if peer.get("network") == tunnel.get("network")),
                None,
            )
            if matching_peer_tunnel is None:
                errors.append(f"{site.get('key')}/{tunnel.get('interface')}: no matching tunnel on {peer_site.get('router')} for {tunnel.get('network')}.")
            else:
                if matching_peer_tunnel.get("local_address") != tunnel.get("remote_address"):
                    errors.append(f"{site.get('key')}/{tunnel.get('interface')}: remote tunnel IP does not match partner local tunnel IP.")
                if matching_peer_tunnel.get("remote_address") != tunnel.get("local_address"):
                    errors.append(f"{site.get('key')}/{tunnel.get('interface')}: partner tunnel remote IP does not point back to this site.")

    if len(router_names) != len(set(router_names)):
        errors.append("Router hostnames must be unique.")
    if len(switch_names) != len(set(switch_names)):
        errors.append("Switch hostnames must be unique.")
    if len(router_ids) != len(set(router_ids)):
        errors.append("OSPF router IDs must be unique.")
    all_addressed_networks = wan_networks + lan_networks + tunnel_networks
    for i, (name1, net1) in enumerate(all_addressed_networks):
        for name2, net2 in all_addressed_networks[i + 1:]:
            if name1 != name2 and net1 != net2 and net1.overlaps(net2):
                errors.append(f"Address-plan overlap: {name1} {net1} overlaps {name2} {net2}.")
    for i, (name1, net1) in enumerate(wan_networks):
        for name2, net2 in wan_networks[i + 1:]:
            if net1.overlaps(net2):
                errors.append(f"WAN network overlap: {name1} {net1} overlaps {name2} {net2}.")

    if global_data.get("project", {}).get("test_server_ip") != "10.10.20.10":
        errors.append("The model's HQ test server is expected at 10.10.20.10; update the tests if changed.")
    policy = global_data.get("security_policy", {})
    for key in ("guest_to_internal", "guest_to_management", "staff_to_guest", "staff_to_management"):
        if policy.get(key) != "deny":
            errors.append(f"Security invariant {key} must remain 'deny'.")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("P3 data validation FAILED:")
        for item in errors:
            print(f"  - {item}")
        return 1
    print("P3 data validation PASSED: site IDs, addresses, VLANs, tunnels and policy invariants are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
