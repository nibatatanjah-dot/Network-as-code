# P1 baseline export location

Export each of the seven current P1 Phase 7 device running-configs into this folder as text files named:

- `HQ-R1.cfg`
- `BR1-R1.cfg`
- `BR2-R1.cfg`
- `HQ-SW1.cfg`
- `BR1-SW1.cfg`
- `BR2-SW1.cfg`
- `ISP.cfg`

Use the device CLI command `terminal length 0` followed by `show running-config`. Do not export to this shared repository until secrets are removed. Replace local usernames/secrets, VPN keys, SNMP communities and other credentials with consistent placeholders. If an unredacted export is required for local comparison, keep it outside Git in a secured local folder.

These baseline files are intentionally not supplied because the P1 document describes the design but not every line of the actual current device configuration. The generated P3 references are not a substitute for capturing the actual running state. The `*.cfg` and `*.conf` patterns in `.gitignore` intentionally ignore baseline exports by default. For local comparison, leave them untracked. If your assessment requires a sanitized baseline in Git, redact and review it first, scan it for credentials, then explicitly `git add -f` only the reviewed file(s); never force-add an unredacted export.
