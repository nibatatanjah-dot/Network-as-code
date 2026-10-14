# Local deployment candidates — intentionally empty

This folder is ignored by Git. Only put reviewed, sanitized-for-secrets, deployment-ready **configuration fragments** here after comparing the proposed change with the current baseline. Do not put the `build/rendered/*.cfg` CI reference snapshots here unchanged.

Expected filenames if you later enable the optional Ansible adapter:

- `HQ-R1.cfg`
- `BR1-R1.cfg`
- `BR2-R1.cfg`
- `HQ-SW1.cfg`
- `BR1-SW1.cfg`
- `BR2-SW1.cfg`

Before using these playbooks:

1. Confirm the device is an SSH-accessible IOS/IOS-XE target, not a Packet Tracer simulated device.
2. Back up the startup and running configurations outside the lab and verify console recovery.
3. Prove `configure replace nvram:startup-config force` works on that exact target.
4. Review and approve the exact fragment and expected post-checks.
5. Create `DEPLOYMENT_READY` locally with the exact phrase `I_RECONCILED_THIS_CANDIDATE_WITH_THE_LAB_BASELINE`. This marker is ignored by Git and checked by the manual deployment readiness script.
