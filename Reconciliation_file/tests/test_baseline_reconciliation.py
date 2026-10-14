"""Regression tests for corrections identified in the supplied P1 baselines."""
from pathlib import Path

# The reconciliation tests are part of the repository-wide suite.  Consume
# the canonical render output produced by scripts/render_configs.py rather
# than creating a second build tree inside Reconciliation_file.
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "build" / "rendered"


def read_config(name: str) -> str:
    """Read a rendered CI/reference configuration by device name."""
    path = OUTPUT / f"{name}.cfg"
    assert path.exists(), f"Run scripts/render_configs.py before pytest ({path} is missing)."
    return path.read_text(encoding="utf-8")


def section(config: str, heading: str, next_heading: str = "!") -> str:
    """Return a simple IOS config section, including its heading."""
    start = config.index(heading)
    end = config.find(f"\n{next_heading}", start)
    return config[start:] if end < 0 else config[start:end]


def test_branch1_staff_dhcp_uses_staff_gateway_and_guest_pool_exists():
    config = read_config("BR1-R1")
    staff_pool = section(config, "ip dhcp pool BRANCH1-STAFF")
    guest_pool = section(config, "ip dhcp pool BRANCH1-GUEST")
    assert "network 10.20.10.0 255.255.255.0" in staff_pool
    assert "default-router 10.20.10.1" in staff_pool
    assert "network 10.20.30.0 255.255.255.0" in guest_pool
    assert "default-router 10.20.30.1" in guest_pool


def test_branch2_gre_tunnel_has_hq_wan_destination():
    config = read_config("BR2-R1")
    tunnel = section(config, "interface Tunnel20")
    assert "tunnel destination 203.0.113.2" in tunnel


def test_branch_switch_management_addresses_match_their_site_subnets():
    br1 = read_config("BR1-SW1")
    br2 = read_config("BR2-SW1")
    assert "ip address 10.20.99.2 255.255.255.0" in section(br1, "interface Vlan99")
    assert "ip default-gateway 10.20.99.1" in br1
    assert "ip address 10.30.99.2 255.255.255.0" in section(br2, "interface Vlan99")
    assert "ip default-gateway 10.30.99.1" in br2


def test_branch2_trunk_has_the_standard_secure_trunk_settings():
    config = read_config("BR2-SW1")
    trunk = section(config, "interface GigabitEthernet0/1")
    assert "switchport mode trunk" in trunk
    assert "switchport nonegotiate" in trunk
    assert "switchport trunk native vlan 999" in trunk
    assert "switchport trunk allowed vlan 10,20,30,99" in trunk


def test_ospf_process_and_tunnel_interface_names_match_p1_baseline():
    assert "router ospf 1" in read_config("HQ-R1")
    assert "interface Tunnel1" in read_config("HQ-R1")
    assert "interface Tunnel20" in read_config("HQ-R1")
    assert "interface Tunnel1" in read_config("BR1-R1")
    assert "interface Tunnel20" in read_config("BR2-R1")


def test_nat_uses_only_explicit_staff_server_and_guest_prefixes():
    for device, site in (("HQ-R1", "10"), ("BR1-R1", "20"), ("BR2-R1", "30")):
        config = read_config(device)
        nat_acl = section(config, "ip access-list standard NAT-LIST")
        assert f"permit 10.{site}.10.0 0.0.0.255" in nat_acl
        assert f"permit 10.{site}.20.0 0.0.0.255" in nat_acl
        assert f"permit 10.{site}.30.0 0.0.0.255" in nat_acl
        assert f"permit 10.{site}.0.0 0.0.255.255" not in nat_acl


def test_management_subinterface_is_not_marked_nat_inside():
    for device in ("HQ-R1", "BR1-R1", "BR2-R1"):
        config = read_config(device)
        mgmt = section(config, "interface GigabitEthernet0/1.99")
        assert "ip nat inside" not in mgmt


def test_branch_server_port_is_parked_when_no_local_server_is_declared():
    # Intentional desired-state change: site data says only HQ has a local server.
    # Confirm the physical port is unused before applying this candidate to a real lab.
    for device in ("BR1-SW1", "BR2-SW1"):
        config = read_config(device)
        port = section(config, "interface FastEthernet0/2")
        assert "switchport access vlan 999" in port
        assert "shutdown" in port
