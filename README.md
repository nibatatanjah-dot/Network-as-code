# P3 — Network-as-Code with a GitOps Workflow

This repository is a complete **starter implementation** for automating the secure HQ + two-branch SME network from P1.

> **Safety boundary:** the generated files under `build/` are reference configurations for CI/Batfish. They are not a drop-in replacement for the actual P1 running-configs. The P1 process document describes the design and partial state, but it does not contain all seven complete current running configurations. Reconcile the templates against your real, sanitized P1 configuration exports before preparing any deployable change. Packet Tracer is not a supported SSH target for Ansible deployment.

## What is included

- YAML source of truth for the three sites, addressing, WAN links, VLANs and security policy.
- Jinja2 templates for three edge routers, three access switches and the ISP router.
- A renderer that uses synthetic, CI-only IPsec keys by default and requires environment secrets for deployment-mode rendering.
- Data validation and pytest checks.
- A Batfish snapshot builder, positive/negative reachability checks, and a bad-change generator.
- An optional read-only pyATS live-device smoke suite, run after successful deployment to a compatible real IOS lab; it is not run against Packet Tracer or normal public PR runners.
- GitHub Actions CI for linting, rendering, automated checks and Batfish analysis.
- An optional, guarded Ansible deployment-and-rollback playbook for a compatible SSH-accessible lab. Deployment remains blocked until you prepare a separate reviewed candidate directory and explicitly verify the target platform and rollback method.
- Pinned optional Ansible and pyATS control-node dependencies and Galaxy collection versions.
- A Windows/VS Code runbook covering exact locations, commands, GitHub setup, test scenarios and report evidence.

## Repository map

```text
P3_Network_as_Code_GitOps/
├── .github/workflows/           # CI and guarded manual deployment workflow
├── data/                        # Authoritative YAML state/policy
├── inventory/                   # Ansible target inventory (documentary placeholders)
├── templates/                   # Jinja2 templates
├── configs/baseline/            # Put sanitized P1 reference exports here
├── configs/deploy/               # Local-only; ignored candidate fragments + readiness marker
├── playbooks/                   # Backup, guarded deployment and rollback
├── scripts/                     # Validate, render, build Batfish snapshot, test
├── tests/                       # Local tests
├── docs/                         # Runbook, architecture, topology, report analysis
├── requirements.txt
└── README.md
```

## Quick start on Windows (PowerShell in VS Code)

1. Extract the ZIP. Open the extracted `P3_Network_as_Code_GitOps` folder in VS Code.
2. Use Python 3.12 or newer, Git, and Docker Desktop with Linux containers enabled. Docker is required for Batfish, not for the YAML/template-only checks.
3. In the VS Code terminal, create and activate a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run the local non-Batfish checks:

   ```powershell
   yamllint -c .yamllint data inventory playbooks .github/workflows requirements-collections.yml docker-compose.yml
   python scripts/validate_data.py
   python scripts/render_configs.py --mode ci --output build/rendered
   python scripts/build_batfish_snapshot.py --configs build/rendered --output build/batfish_snapshot
   pytest -q
   ```

5. Start Batfish from Docker Compose in one terminal:

   ```powershell
   docker compose up -d batfish
   ```

6. In another terminal, wait for Batfish and run the network checks:

   ```powershell
   python scripts/wait_for_batfish.py --host localhost --port 9996
   python scripts/batfish_validate.py --snapshot-dir build/batfish_snapshot --host localhost --port 9996
   ```

7. Stop the Batfish container when finished:

   ```powershell
   docker compose down
   ```

If your computer uses a different Python launcher, use the Python 3.12 interpreter installed on your machine and replace `py -3.12` accordingly.

## Important security rules

- Never commit real device passwords, VPN pre-shared keys, private keys, or complete unredacted running-configs.
- `--mode ci` uses a known synthetic key solely so the candidate can be parsed and tested. **Do not deploy that output.**
- `--mode deployment` requires `P3_IPSEC_PSK_HQ_BR1` and `P3_IPSEC_PSK_HQ_BR2` from the shell environment and writes to an ignored local build folder. It still does not make the generated reference configuration safe to replace a live P1 configuration.
- The sample Ansible inventory contains documentation-only addresses and explicitly false verification flags. Replace them only for a separate SSH-accessible test lab after a backup and rollback test.
- Ansible network-control tasks and the optional pyATS suite should run under WSL2/Linux, not native Windows PowerShell. See Phase 9 of the runbook.
- The guarded deployment playbook requires an explicit confirmation, `deployment_verified: true` for each host, and local deployment files. Do not target Packet Tracer simulated devices.
- GitHub-hosted runners cannot reach your laptop's private lab by default. An actual CI deployment requires a properly secured self-hosted runner inside the lab network and a supported device API/SSH interface.

## Why both a positive and a negative Batfish test exist

The positive check expects HQ Staff HTTPS to the modeled HQ server to be reachable. The negative check expects HQ Guest HTTPS to that server to be blocked. The positive control prevents a broken or disconnected model from making every security test pass vacuously.

To demonstrate a failure safely, first build a normal snapshot, then run:

```powershell
python scripts/make_bad_change.py --source build/rendered --output build/bad-change
python scripts/build_batfish_snapshot.py --configs build/bad-change --output build/bad-snapshot
python scripts/batfish_validate.py --snapshot-dir build/bad-snapshot --host localhost --port 9996
```

The last command is expected to exit non-zero because the bad candidate permits HQ Guest to reach the HQ server. This is a deliberate negative test, not a successful production configuration.

## Start here

Follow `docs/IMPLEMENTATION_RUNBOOK.md` in order. Do not skip the baseline reconciliation and deployment-feasibility steps. The rendered candidate configs and actual Batfish service cannot be validated in this generated bundle alone; run the included local checks on your machine, then run the Docker/Batfish integration checks in the runbook. The Batfish service uses the dated tag `batfish/allinone:test-2026.10.06.3806` checked on 2026-10-14; upgrade this tag deliberately and re-run the integration tests when changing it.
