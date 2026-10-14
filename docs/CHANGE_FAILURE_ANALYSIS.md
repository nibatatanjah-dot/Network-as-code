# Change-failure analysis (complete with actual evidence)

## Scenario

A proposed change places `permit ip any 10.0.0.0 0.255.255.255` before the deny statement in the HQ `GUEST-IN` access list. This grants guest systems reachability into private internal networks, including the HQ server subnet. Treat this as an intentionally dangerous change and use the isolated generated snapshot only.

## Expected Network-as-Code result

1. The change is proposed on a feature branch.
2. YAML/template rendering succeeds because the text may be syntactically valid.
3. Batfish evaluates the candidate and discovers successful HQ Guest HTTPS reachability to the HQ server.
4. The security assertion fails. The pull request does not satisfy the required status check and must not be merged/deployed.
5. The engineer removes the permissive rule or restores the deny-first policy, pushes a correction and reruns CI.

## Manual CLI comparison

If an engineer applies the permissive ACL line directly to the router before analysis, the access list may permit guest traffic into the internal network. If the command is applied at only one site or one device, the network can also become inconsistent. Device logging may still provide useful records, but it is not equivalent to a peer-reviewed desired-state change linked to a successful policy test.

## Evidence to attach

| Evidence | File/screenshot to attach | Actual result |
|---|---|---|
| Clean CI run | GitHub Actions successful run | Fill in after execution |
| Staff-to-server positive control | Batfish output | Fill in after execution |
| Guest-to-server negative control | Batfish output | Fill in after execution |
| Intentionally unsafe candidate | Local script output and Batfish failure | Fill in after execution |
| PR review and merge protection | GitHub PR / branch rules screenshot | Fill in after setup |
| Deployment rollback | Ansible log and post-rollback functional tests, only if performed | Write “Not executed — no compatible SSH lab” if applicable |

## Lessons to discuss

- Syntax validation does not prove that a network policy is safe.
- A positive control helps distinguish a genuinely blocked flow from a broken or incomplete test model.
- The policy check must run on the rendered candidate rather than only the old baseline.
- Approval and successful validation are separate controls.
- Rollback must restore the device state, then operational tests must verify the recovery; a Git revert by itself is not proof of network recovery.
- Actual conclusions must be based on the collected output, not on the expected results written in advance.
