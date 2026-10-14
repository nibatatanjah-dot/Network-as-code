# P1 baseline to P3 desired-state reconciliation

Date: 2026-10-14

## Purpose and safety boundary

The sanitized `configs/baseline/*.cfg` files record the user-supplied Packet Tracer `show running-config` outputs. They are observations, not intended deployment inputs. Generated files in `build/rendered/` are a proposed reference state produced from YAML and Jinja2. They must not be pasted into Packet Tracer as whole configurations or deployed to a live device without a separate review and rollback rehearsal.

This reconciliation updates the model for consistency with the known P1 addressing and interface design, and it adds the security controls intended by P3. It does not claim the candidate has been applied to the actual Packet Tracer devices.

## Corrections represented in the desired state

| Device | Observed P1 issue | P3 desired state | Why |
|---|---|---|---|
| BR1-R1 | DHCP pool `STAFF` assigns default gateway `10.20.30.1` instead of `10.20.10.1` | Staff pool gateway is `10.20.10.1` | Prevents clients in the Staff pool being given the Guest gateway |
| BR1-R1 | No Guest DHCP pool appears in the supplied output | Add `GUESTS` pool for `10.20.30.0/24` with gateway `10.20.30.1` | Supports Guest DHCP on all sites |
| BR2-R1 | GRE tunnel has no `tunnel destination` in the supplied output | `Tunnel1` destination is HQ WAN `203.0.113.2` | Provides the defined hub-and-spoke GRE peer |
| BR1-SW1 | VLAN 99 SVI is `10.10.99.2` (HQ range) | `10.20.99.2/24`, gateway `10.20.99.1` | Uses the Branch 1 management subnet |
| BR2-SW1 | VLAN 99 SVI is `10.10.99.2` (HQ range) | `10.30.99.2/24`, gateway `10.30.99.1` | Uses the Branch 2 management subnet |
| BR2-SW1 | Trunk is missing native VLAN 999, allowed VLAN list and `switchport nonegotiate`; has leftover access VLAN 10 | Standard trunk: native 999, allowed 10,20,30,99, DTP negotiation disabled | Makes trunk policy consistent with HQ and Branch 1 |
| BR2-R1 | Guest DHCP pool is called `GEUSTS` | Use consistent pool name `GUESTS` | Naming consistency; the misspelling alone does not prove DHCP is broken |
| All routers | Existing OSPF process ID is 1 | Retain process ID 1 | Avoid unnecessary local configuration drift |
| All routers | Existing tunnel interface names are `Tunnel1` (and HQ `Tunnel2`) | Retain those names | Reduces unnecessary churn and eases comparison |
| All routers | Existing NAT ACL is `NAT-LIST` with explicit Staff, Servers and Guests `/24` prefixes | Retain `NAT-LIST` name and permit those explicit prefixes | Avoids broadening NAT matching to the entire site `/16` |
| All routers | VLAN 99 subinterface was not shown as a NAT-inside interface | Do not enable `ip nat inside` on VLAN 99 | Management should not be included in data-VLAN NAT policy |

## Intentional security changes beyond the observed baseline

These controls are intended by the P3 model, but they differ from the pasted running configurations. Treat each as a reviewed policy change, not as a harmless formatting correction:

- Router ACLs are generated to isolate Guest traffic from private `10.0.0.0/8` networks and restrict Staff and Management flows.
- GRE traffic is intended to be protected by IPsec. The pasted P1 configurations did not show the IPsec crypto configuration, so P1 tunnel encryption must not be claimed based on these snapshots.
- Switch candidates enable DHCP snooping, Dynamic ARP Inspection and access-port security.
- The Branch 1/Branch 2 Fa0/2 candidate ports are parked in VLAN 999 and shut because the current P3 data says `server_attached: false`. **Check that no device is connected to those ports before considering this change.** The supplied P1 snapshots currently configure Fa0/2 as VLAN 20 and do not prove physical occupancy.
- Branch switch management addresses and BR2-SW1 trunk settings are corrected as above.

## Additional pre-deployment blockers to resolve

1. HQ-R1 has `login local` on VTY lines but the pasted config shows no local `username` entry. Validate console access and secure SSH authentication separately. Do not change VTY authentication remotely without a working tested account.
2. BR2-SW1 uses `login` rather than `login local` on VTY lines; verify and standardize in a separately approved management-access change.
3. The pasted router configurations do not show the intended Guest-isolation ACLs or IPsec crypto-map setup. Confirm the actual P1 design status and test new security policy in the simulator before any deployment.
4. The ISP snapshot has no address on Loopback0 and no route to an actual test endpoint. The P3 reference model adds an explicitly simulated `8.8.8.8/32` loopback. This is a modeled test target, not a connection to the public Internet.
5. Templates are generated reference configurations, not complete replacement `show running-config` files. Credentials, authentication configuration, device-specific supported syntax and rollback behavior require separate review.

## Validation commands

Run at the repository root with the project virtual environment active:

```powershell
python scripts/validate_data.py
python scripts/render_configs.py --mode ci --output build/rendered
python -m pytest -q
```

Expected local result after the reconciliation update: data validation passes and all 16 unit tests pass. CI mode uses synthetic credentials and is only for validation. Never deploy CI-mode output.

## Review checklist before any live lab deployment

- [ ] Compare all seven baseline snapshots against rendered candidates.
- [ ] Confirm branch `Fa0/2` ports are not in use before parking them.
- [ ] Confirm supported syntax for the chosen IOS/platform, especially IPsec and switch hardening.
- [ ] Verify local administrator authentication and out-of-band/console recovery.
- [ ] Verify a full backup and rollback method on the actual target.
- [ ] Run Batfish assertions against the candidate snapshot.
- [ ] Deploy only to a disposable, reachable lab after explicit review.
- [ ] Run post-deployment reachability and security tests and retain evidence.
