# P3 final report outline

1. **Title and abstract** — Network-as-Code with GitOps for a secure HQ + two-branch SME network.
2. **Problem statement** — risks of manual drift, accidental ACL errors, missing review and difficult rollback.
3. **Objectives and requirements** — source of truth, templating, Git reviews, lint/validation, deployment approval and rollback.
4. **Existing P1 environment** — actual device inventory, topology, VLANs, IP plan, WAN/VPN, policy and current baseline; attach sanitized evidence.
5. **First-principles design decisions** — YAML over duplicated CLI, Jinja2 templates, Git as desired-state history, Batfish as pre-deployment model checker, Ansible for supported target deployment.
6. **Architecture** — include `ARCHITECTURE.md` workflow and tool responsibility explanation.
7. **Implementation** — repository tree, sample YAML, one template and the corresponding generated config diff.
8. **CI/CD configuration** — lint, source data validation, rendering, tests, Batfish job, GitHub branch protection and PR approval.
9. **Network validation** — parse results and positive/negative reachability tests, plus limitations/warnings.
10. **Bad-change experiment** — the deliberately permissive ACL, expected and actual failure output, corrected version.
11. **Deployment and rollback** — report only what was truly run. If no compatible SSH lab existed, state that the Ansible deployment/rollback adapter was prepared but not executed against Packet Tracer.
12. **Change-failure comparison** — Network-as-Code vs manual CLI (use actual evidence).
13. **Limitations** — Packet Tracer API limitations, Batfish parser support, legacy VPN settings in the reference snapshot, and any GitHub plan constraints.
14. **Lessons learned and conclusion**.
15. **Appendices** — sanitized configs, YAML, workflow YAML, playbooks, test cases, command output and screenshots.
