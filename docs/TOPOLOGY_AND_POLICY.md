# Reference topology, addressing and security policy

This file translates the P1 design record into a structured reference used by the P3 templates. Confirm every line against the real P1 lab before treating it as authoritative.

## Topology

- `ISP` simulates the external network.
- `HQ-R1` connects the HQ switch `HQ-SW1` and has GRE/IPsec tunnels to both branches.
- `BR1-R1` connects `BR1-SW1` and tunnels to HQ.
- `BR2-R1` connects `BR2-SW1` and tunnels to HQ.
- Each site router uses `GigabitEthernet0/0` as the WAN link and `GigabitEthernet0/1` as the 802.1Q LAN trunk in this reference. Verify the actual physical port mapping in Packet Tracer before using the template output.
- Each site switch uses `GigabitEthernet0/1` as the router trunk in this reference. The access ports are FastEthernet0/1 Staff, Fa0/2 server at HQ only, Fa0/3 Guest, Fa0/4 Management, and Fa0/5 a normally-shut rogue-DHCP test port.

## WAN and tunnel links

| Link | Network | ISP side | Site side |
|---|---|---|---|
| HQ–ISP | `203.0.113.0/30` | `203.0.113.1` | HQ `203.0.113.2` |
| Branch 1–ISP | `198.51.100.0/30` | `198.51.100.1` | Branch 1 `198.51.100.2` |
| Branch 2–ISP | `192.0.2.0/30` | `192.0.2.1` | Branch 2 `192.0.2.2` |
| HQ–BR1 tunnel | `172.16.0.0/30` | HQ `.1` | BR1 `.2` |
| HQ–BR2 tunnel | `172.16.0.4/30` | HQ `.5` | BR2 `.6` |

The WAN addresses come from documentation ranges and are for simulation/lab use, not public routable addresses. The reference ISP uses `8.8.8.8/32` on a loopback as a simulated test IP; it is not a real Internet resolver/service.

## LAN prefixes

| VLAN | Purpose | HQ | Branch 1 | Branch 2 |
|---|---|---|---|---|
| 10 | Staff | `10.10.10.0/24` | `10.20.10.0/24` | `10.30.10.0/24` |
| 20 | Servers | `10.10.20.0/24` | `10.20.20.0/24` | `10.30.20.0/24` |
| 30 | Guests | `10.10.30.0/24` | `10.20.30.0/24` | `10.30.30.0/24` |
| 99 | Management | `10.10.99.0/24` | `10.20.99.0/24` | `10.30.99.0/24` |
| 999 | Native/unused parking | no user subnet | no user subnet | no user subnet |

Router gateway convention: `.1` in each VLAN. Switch management convention: `.2` in VLAN 99. Test hosts use `.100` for the modeled Staff/Guest hosts; the HQ server uses `10.10.20.10`.

## Intended policy invariants

- Guest VLAN: DHCP plus HTTP, HTTPS and DNS to external destinations; deny all `10.0.0.0/8` destinations and deny other traffic by default.
- Staff VLAN: allow specified web/DNS/SMB access to the HQ server and web/DNS Internet protocols; deny Guest, Management and other internal access by default.
- Server VLAN: allow established internal TCP replies, DNS responses and update protocols; deny other traffic by default. The reference only models a server physically attached at HQ.
- Management VLAN: allow SSH/HTTPS/ICMP only toward internal site prefixes; deny by default otherwise.
- Switch trunks: native VLAN 999; allowed VLANs 10,20,30,99. VLAN 999 is intentionally not in the allowed list. Confirm how your target platform treats an excluded native VLAN.
- Switch hardening: DHCP snooping for VLANs 10/30, DAI for VLANs 10/30, access-port port security, unused ports parked in VLAN 999 and shut down, and the test port shut down except during a controlled exercise.

## Known limitations

1. The reference router template is a candidate model, not a reconstruction of every line in P1's actual running-config.
2. The reference uses IKEv1/DH group 2 to approximate the P1 Packet Tracer-era VPN model. These legacy lab settings are not a recommendation for new production VPNs.
3. Batfish cannot prove the correctness of any unsupported/unparsed line. Review `fileParseStatus` and `initIssues` results.
4. Packet Tracer cannot be treated as a general SSH-based target for Ansible deployment and `configure replace` rollback.
5. The reference switch config contains platform-specific hardening commands; validate their support in the target simulator/IOS image before applying.
