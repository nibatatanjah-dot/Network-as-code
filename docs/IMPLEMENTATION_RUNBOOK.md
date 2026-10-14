# P3 implementation runbook — Windows + VS Code

This is the step-by-step working procedure. Follow the order; each phase has a gate. The project deliberately separates **CI reference configuration** from **deployable changes**, because Packet Tracer itself is not a normal SSH automation target and the supplied P1 write-up does not expose every current running-config line.

## Phase 0 — Verify tools and capture the P1 baseline

### 0.1 Confirm the lab state

Your P1 process record identifies these seven devices:

- Routers: `HQ-R1`, `BR1-R1`, `BR2-R1`, `ISP`
- Switches: `HQ-SW1`, `BR1-SW1`, `BR2-SW1`

It documents VLANs 10, 20, 30, 99 and 999; site prefixes `10.10.x.0/24`, `10.20.x.0/24` and `10.30.x.0/24`; WAN /30 links; two HQ-to-branch GRE tunnels; OSPF; IPsec; NAT; ACLs; and Layer 2 hardening. Check all addresses and interface labels on your current Packet Tracer file before relying on these reference values.

### 0.2 Export sanitized running configurations

On each device CLI, run:

```text
terminal length 0
show running-config
```

Copy the output to a local text file with the exact filename listed in `configs/baseline/README.md`. Remove or replace sensitive data before committing anything. Do not copy actual pre-shared keys, password hashes, private keys, or user secrets into Git. If the P1 configs differ from the reference topology in this repository, the actual tested P1 state wins; update YAML and templates to match it.

For Packet Tracer devices, CLI support varies by device/model and version. If `terminal length 0` is not accepted, use `show running-config` and manually confirm the output is complete, without paging/truncation.

### 0.3 Check required local tools

In PowerShell:

```powershell
git --version
py -0p
docker --version
docker compose version
```

Install Git, Python 3.12+, VS Code and Docker Desktop if any command is missing. Start Docker Desktop before attempting to run Batfish.

**Gate 0:** you have a saved `.pkt` file, a readable sanitized baseline for each device, and know whether a separate SSH-accessible lab exists. Do not deploy to Packet Tracer.

## Phase 1 — Open and initialize the repository

1. Extract the project ZIP to a stable folder, for example `D:\P3_Network_as_Code_GitOps`.
2. Open that folder in VS Code using **File → Open Folder**.
3. Select **Terminal → New Terminal** and confirm the terminal is PowerShell in the project root.
4. Create and activate a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Run the source-of-truth validator:

   ```powershell
   python scripts/validate_data.py
   ```

   Expected message: `P3 data validation PASSED...`

6. Lint source YAML:

   ```powershell
   yamllint -c .yamllint data inventory playbooks .github/workflows requirements-collections.yml docker-compose.yml
   ```

**Gate 1:** both commands return exit code 0. If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal only, then activate again. This changes only the current PowerShell process.

## Phase 2 — Generate the reference device configurations

From the project root, run:

```powershell
python scripts/render_configs.py --mode ci --output build/rendered
```

Open `build/rendered` in VS Code. It should contain exactly:

- `HQ-R1.cfg`, `BR1-R1.cfg`, `BR2-R1.cfg`
- `HQ-SW1.cfg`, `BR1-SW1.cfg`, `BR2-SW1.cfg`
- `ISP.cfg`

Use VS Code's diff editor to compare the generated reference output with each sanitized file from `configs/baseline`. The goal is to map repeated, parameterized elements to YAML/Jinja2, not blindly replace the working P1 config.

Important differences to reconcile before any candidate is considered deployable include physical interface names, existing ACL names/rules/order, VPN peer keys and crypto settings, device usernames/SSH settings, DHCP exclusions, interface states, NAT rules, OSPF process/router IDs, switch port mapping, snooping/DAI settings, and commands unsupported by your specific Packet Tracer release.

Do not paste `build/rendered/*.cfg` directly into Packet Tracer, an IOS device, or the Ansible deployment folder. These are model/reference files with synthetic keys and no actual management credentials.

**Gate 2:** seven reference files are generated, no tracked file contains a real secret, and you can explain which Jinja2 variable controls each site's addressing/interface-specific difference.

## Phase 3 — Create the Batfish snapshot

Run:

```powershell
python scripts/build_batfish_snapshot.py --configs build/rendered --output build/batfish_snapshot
```

Expected structure:

```text
build/batfish_snapshot/
  configs/        # seven generated router/switch configs
  hosts/          # HQ Staff, HQ Guest, two branch Guests and HQ Server JSON
```

The modeled hosts make reachability assertions meaningful. Without a source host or destination host model, an empty reachability result could be caused by missing topology rather than a successful security control.

## Phase 4 — Start and run Batfish

Open a terminal in the project root and start Batfish:

```powershell
docker compose up -d batfish
docker compose ps
```

Wait until Batfish responds:

```powershell
python scripts/wait_for_batfish.py --host localhost --port 9996 --timeout 180
```

Then run:

```powershell
python scripts/batfish_validate.py --snapshot-dir build/batfish_snapshot --host localhost --port 9996
```

The expected assertions are:

1. **Positive control:** HQ Staff HTTPS to the HQ server succeeds.
2. **Negative security control:** HQ Guest HTTPS to the HQ server has no successful path.

Batfish will print file-parse status and initialization issues. Review parser warnings—especially if any of your actual P1 commands are unsupported. The script fails on a file parse `FAILED` status, a missing positive flow, or a successful guest-to-server flow.

If Docker does not start the service, run `docker compose logs batfish` and check Docker Desktop is using Linux containers with sufficient memory. To stop Batfish after testing:

```powershell
docker compose down
```

**Gate 4:** both positive and negative assertions pass on the normal candidate, and parse warnings have been reviewed rather than ignored.

## Phase 5 — Demonstrate a bad change caught by CI

This negative test never touches a device.

1. Make sure the clean build exists (`build/rendered`).
2. Make an unsafe copy:

   ```powershell
   python scripts/make_bad_change.py --source build/rendered --output build/bad-change
   python scripts/build_batfish_snapshot.py --configs build/bad-change --output build/bad-snapshot
   ```

3. Run Batfish against the bad snapshot:

   ```powershell
   python scripts/batfish_validate.py --snapshot-dir build/bad-snapshot --host localhost --port 9996
   ```

4. The **expected result is a failure** that says guest-to-server reachability exists. Exit code 1 is expected for this negative test. It proves the assertion detects the bad policy; do not treat it as a failed normal build.

To record evidence, capture the clean successful Batfish run and the deliberate bad-change failure. Do not commit the `build/` directory.

## Phase 6 — Put the project on GitHub

Run in the project root:

```powershell
git init
git branch -M main
git add .
git status --short
```

Inspect `git status --short` carefully. It must not include `build/`, `.venv/`, unredacted baseline exports, local deployment candidates or secrets. Then:

```powershell
git commit -m "Initialize P3 Network-as-Code project"
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPO.git
git push -u origin main
```

If Git says the remote already exists, inspect it with `git remote -v` and correct it rather than adding another blindly. Replace the example URL with the repository you created on GitHub.

The repository includes `.github/workflows/network-ci.yml`; GitHub should start the workflow when you push. Open GitHub → **Actions** → **Network-as-Code CI**. Check both jobs: lint/render/unit tests and Batfish policy checks.

If Actions did not appear, verify the repository's Actions settings, default branch and that `.github/workflows/network-ci.yml` is in the pushed branch.

## Phase 7 — Use a feature branch and pull request

```powershell
git switch -c feature/document-network-baseline
```

Make one small, reviewable change (for example, document a verified interface mapping or adjust a YAML comment/value that does not change policy). Then:

```powershell
git add data docs
git diff --cached
git commit -m "Document network source of truth"
git push -u origin feature/document-network-baseline
```

Open a PR from the feature branch into `main`. Confirm that all CI checks pass before merging. In repository **Settings → Branches** or **Rules → Rulesets**, protect `main` and require a pull request and the `lint-render-test` and `batfish-policy-checks` status checks. For a real independent approval, another account/user with the required repository access must review and approve the PR; do not represent your own self-review as independent approval.

GitHub environment required-reviewer availability depends on repository visibility and plan. If using GitHub Free with a private repository, required reviewers for environments may not be available; branch/PR checks and a human lab operator gate should remain in place rather than claiming that an unavailable environment gate is enforced.

**Gate 7:** at least one feature branch/PR has run CI, the policy checks are visible, and `main` is protected against direct pushes as far as your plan supports.

## Phase 8 — Reconcile candidate output with P1 before deployment

This phase converts a reference into a real deployable change; it is not safe to skip.

1. Compare `build/rendered/<device>.cfg` with the real P1 baseline export.
2. Preserve tested P1 management accounts, SSH settings, secrets, interface names, port assignments and all working VPN/NAT/OSPF configuration that is not part of the proposed change.
3. Modify the YAML/Jinja2 so the generated candidate expresses the desired state without removing an unrelated tested feature.
4. Create a change-specific fragment containing only the reviewed commands to apply. Put it locally in `configs/deploy/<device>.cfg`; that folder is ignored by Git by design. These must be minimal reviewed change fragments, not the full CI render.
5. Confirm the device platform supports SSH/network_cli and that the intended rollback command works on a disposable target. Packet Tracer does not satisfy this requirement.
6. Back up the running and startup configurations separately. Test console recovery and make sure the backup can restore the previous state.
7. Set `deployment_verified: true` and `p3_rollback_method_verified: true` only for the hosts on which you have completed these checks. Update `inventory/hosts.yml` to use the real management IPs and accounts for the disposable lab. Never use the documentation TEST-NET addresses.
8. For local testing, point the candidate-directory environment variable at the ignored local folder and create a local-only readiness marker:

   ```powershell
   $env:P3_CANDIDATE_DIR = (Resolve-Path "configs/deploy").Path
   Set-Content (Join-Path $env:P3_CANDIDATE_DIR "DEPLOYMENT_READY") "I_RECONCILED_THIS_CANDIDATE_WITH_THE_LAB_BASELINE"
   ```

   For a GitHub self-hosted runner, keep candidate files and this marker in a separate private folder outside the checkout and set the repository variable `P3_CANDIDATE_DIR` to that absolute path.

9. Set a one-terminal-only confirmation before running the readiness check:

   ```powershell
   $env:P3_ENABLE_DEPLOYMENT = "YES_I_HAVE_A_DISPOSABLE_LAB"
   python scripts/check_deployment_ready.py
   ```

The placeholder scan checks for obvious mistakes, not whether the change is safe. Read and review every command before proceeding.

## Phase 9 — Run a controlled deployment/rollback demo (optional; compatible disposable lab only)

**Do not run Ansible against Cisco Packet Tracer devices.** Ansible's network CLI controller must run on Linux/WSL2 or another supported Unix-like control node. This phase is optional; if you have only Packet Tracer, document deployment/rollback as not executed and finish the CI/Batfish demonstration.

### 9.1 Prepare a Linux control node in WSL2

From an elevated Windows PowerShell window, install Ubuntu 24.04 if it is not already installed, following Microsoft's current WSL instructions. After setup, open Ubuntu and run:

```bash
python3 --version
sudo apt update
sudo apt install -y python3-venv python3-pip git openssh-client
```

Use a Python 3.12+ installation for `ansible-core==2.21.5`. From the WSL shell, enter the Windows project folder (update the drive/folder if yours differs):

```bash
cd /mnt/d/P3_Network_as_Code_GitOps
python3 -m venv .venv-ansible
source .venv-ansible/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-ansible.txt
ansible-galaxy collection install -r requirements-collections.yml
ansible --version
ansible-galaxy collection list
```

If your project is not stored at `D:\P3_Network_as_Code_GitOps`, replace `/mnt/d/P3_Network_as_Code_GitOps` with its actual WSL path. Keep the ordinary `requirements.txt` Windows environment and the optional `.venv-ansible` WSL environment separate.

### 9.2 Prepare private candidate files outside the Git checkout (recommended)

A GitHub self-hosted runner cleans its checkout during jobs. Therefore, the actual reviewed candidate files and marker should live in a private folder outside the repository working tree. On local WSL you may use the ignored folder for the optional exercise; on the self-hosted runner configure a separate directory such as `/srv/p3-candidates` and set the repository variable `P3_CANDIDATE_DIR` to that absolute path.

Create one **change-specific command fragment** for each target (`HQ-R1.cfg`, `BR1-R1.cfg`, `BR2-R1.cfg`, `HQ-SW1.cfg`, `BR1-SW1.cfg`, `BR2-SW1.cfg`) only after comparing generated reference output with the sanitized P1 baseline. Do not use the full CI-rendered reference as a replacement for your full running configuration. Keep all such candidates private and out of Git.

For a local WSL lab, point the environment variable to the local ignored folder:

```bash
export P3_CANDIDATE_DIR="$(pwd)/configs/deploy"
```

On the controlled runner, place candidates in the configured external folder and define GitHub repository variable `P3_CANDIDATE_DIR` accordingly. Do not expose candidate files or network credentials to untrusted pull-request workflows.

### 9.3 Prove management access and recovery before deploying

1. Confirm direct SSH access to each target, and that console/out-of-band recovery is available.
2. Verify actual IOS/IOS-XE platform and interface names; check every command in the proposed fragments.
3. Back up running config to the controller and separately save the pre-change working state to startup configuration.
4. On a disposable target of the exact same device/image, prove that `configure replace nvram:startup-config force` is supported and restores the expected configuration.
5. Edit `inventory/hosts.yml`: replace all six documentation TEST-NET `ansible_host` values with real management IPs. Set `deployment_verified: true` and `p3_rollback_method_verified: true` under each host **only after** that host has passed SSH and rollback checks.
6. Put the exact reconciliation marker in the candidate directory:

   ```bash
   printf '%s\n' 'I_RECONCILED_THIS_CANDIDATE_WITH_THE_LAB_BASELINE' > "$P3_CANDIDATE_DIR/DEPLOYMENT_READY"
   ```

7. Set the one-shell confirmation, using a dummy/lab-only workflow secret only for the disposable lab:

   ```bash
   export P3_ENABLE_DEPLOYMENT='YES_I_HAVE_A_DISPOSABLE_LAB'
   python scripts/check_deployment_ready.py
   ```

The readiness check must reject missing candidates, placeholder TEST-NET inventory addresses, and hosts whose verification flags are not explicitly true. A pass is only a prerequisite; it does not establish that a candidate is safe.

### 9.4 Back up and test the rollback playbook

With the WSL virtual environment active and inventory set to verified lab addresses:

```bash
ansible-playbook playbooks/backup.yml --limit HQ-R1
```

Read the output and verify that the backup file exists in `evidence/backups/HQ-R1/`. Then run the forced failure demo against **one disposable router only**:

```bash
ansible-playbook playbooks/deploy_with_rollback.yml \
  --limit HQ-R1 \
  -e confirm_lab_deployment=true \
  -e force_rollback_demo=true
```

The command is expected to finish as failed because the playbook intentionally raises a failure after applying the candidate. Its rescue block should invoke configuration replace and confirm the device responds. Immediately rerun the project-specific routing, reachability and ACL tests; `show ip interface brief` alone does not prove all network behavior has been restored.

If the device is unreachable, the rollback command is unsupported, or you cannot confirm the restored state, stop and recover through console/known-good backup. Never test this sequence on your P1-only Packet Tracer topology.

### 9.5 Optional pyATS read-only smoke checks

pyATS is deliberately separate from normal pull-request CI because it must connect to actual lab devices. The testbed builder reads the target IPs from `inventory/hosts.yml` and uses environment-variable references for secrets. The checks do not make configuration changes.

With a compatible IOS lab, a verified inventory, and the WSL environment active:

```bash
python scripts/build_pyats_testbed.py --inventory inventory/hosts.yml --output build/pyats_testbed.yml
python -m pip install -r requirements-pyats.txt
export P3_DEVICE_USERNAME='your-lab-username'
export P3_DEVICE_PASSWORD='your-lab-password'
export P3_ENABLE_PASSWORD='your-lab-enable-password'
python tests/pyats/network_smoke.py --testbed build/pyats_testbed.yml
```

Do not put actual values in shell scripts, YAML or Git. The sample inventory intentionally uses TEST-NET addresses, so the testbed builder should refuse until the inventory has been updated to real lab management IPs. The smoke suite checks that all six devices answer `show version`, each switch contains VLANs 10/20/30/99/999, and the reference router/switch uplinks report up/up. If your true P1 interface names differ from this reference, edit `REQUIRED_UPLINKS` in `tests/pyats/network_smoke.py` after comparing your baseline.

The manual GitHub deployment workflow runs these checks only after a normal successful deployment. It skips pyATS on the intentional rollback demo because that job is expected to report a failed deployment step; run pyATS separately after the rollback to obtain post-recovery evidence.

### 9.6 Optional GitHub Actions deployment

The manual workflow uses a **dedicated, locked-down self-hosted runner** labelled `network-lab`, because GitHub-hosted runners cannot reach your private home lab by default. Do not attach an internet-exposed general-purpose computer with production credentials as a self-hosted runner.

Configure repository variable `P3_CANDIDATE_DIR` to the candidate folder on that runner, and secrets `P3_ENABLE_DEPLOYMENT`, `P3_DEVICE_USERNAME`, `P3_DEVICE_PASSWORD`, and `P3_ENABLE_PASSWORD` with lab-only values. Prepare the same reviewed candidate files and marker in that external folder. The workflow only accepts a manual dispatch against `main` plus the exact confirmation phrase. If this isolated runner has not been built and security-reviewed, skip this optional stage and do not claim a live GitHub deployment was executed.

## Phase 10 — Write the report and collect evidence

Capture screenshots/logs of:

- actual P1 baseline and sanitized export inventory;
- repository structure and source-of-truth YAML;
- one generated configuration diff showing shared template + site-specific data;
- successful clean CI run and passing Batfish assertions;
- the intentionally bad candidate and its Batfish failure;
- PR review and CI status checks;
- only if performed, a supported lab deployment, a controlled forced rollback, and post-rollback functional verification.

Use `docs/CHANGE_FAILURE_ANALYSIS.md` as the report section. Mark deployment/rollback evidence as **not executed** if no compatible SSH lab is available. A code-level mock or a restored generated file must not be described as a live-device rollback.
