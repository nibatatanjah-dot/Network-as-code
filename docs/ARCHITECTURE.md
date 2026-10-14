# Architecture and workflow

## Responsibilities

- **Source of truth:** `data/global.yml` and `data/sites.yml` describe VLANs, addressing, links, per-site identity and security invariants.
- **Templating:** `templates/*.j2` turn the structured state into IOS-style router/switch/ISP reference snapshots. The templates are for modelling and review; they must be reconciled against actual P1 baseline exports before deployment.
- **Fast CI:** yamllint detects YAML style/syntax problems; `validate_data.py` checks IP address consistency, site IDs, VLAN invariants and tunnel definitions; Jinja2 StrictUndefined fails when a required template value is absent; pytest verifies specific policy and rendering expectations.
- **Network validation:** Batfish parses candidate configs and checks expected reachability. A positive control (HQ Staff → HQ Server HTTPS) and negative control (HQ Guest → HQ Server HTTPS) are both required.
- **Review:** changes are proposed in a feature branch, checked by GitHub Actions, reviewed, and merged through a PR.
- **Deployment:** optional guarded Ansible path for compatible SSH-accessible IOS/IOS-XE devices; not Packet Tracer.
- **Post-deployment smoke checks:** the optional pyATS suite connects read-only to the devices to verify CLI availability, expected VLANs on the switches and required uplinks in an up/up state. It uses addresses from the same Ansible inventory and credentials from environment variables.
- **Recovery:** controller-side backup plus a saved pre-change startup configuration. On post-check failure, the playbook issues `configure replace nvram:startup-config force`. This is valid only where this command is supported and has been proven on the target. If it is unsupported, do not use this adapter; implement the platform's verified rollback mechanism instead.

## CI job sequence

```text
PR or push
  ├── YAML lint
  ├── Validate IP/site/VLAN/policy invariants
  ├── Render seven CI-only device snapshots
  ├── Build Batfish snapshot with modeled hosts
  └── Unit tests
        ↓
  Batfish service job
    ├── check parse status / initialization warnings
    ├── expect Staff HTTPS → HQ Server succeeds
    └── expect Guest HTTPS → HQ Server has no successful path
```

The CI render uses only synthetic IPsec keys. It does not connect to or change a network device. If Batfish cannot parse a required part of the model, CI should fail or the warnings must be reviewed and the model adjusted; unsupported commands cannot be silently treated as verified policy.

## Deployment and rollback separation

The GitHub-hosted CI job cannot normally reach private devices behind the user's router/firewall. A deployment job would require a secured self-hosted runner inside the target lab network or a deliberately designed management path. The provided `deploy-lab.yml` is manual, requires `main`, a typed confirmation and the `network-lab` environment. It must remain unused until a real compatible target, its credentials, protected environment and local candidate files exist.

## Trust boundary

Nothing from pull-request text, branch names or YAML data should be executed as shell code. Secrets are injected from environment/secret storage and do not belong in YAML or generated artifacts. Do not use `pull_request_target` to run untrusted branch code with write permissions. The CI workflow uses read-only repository permissions.
