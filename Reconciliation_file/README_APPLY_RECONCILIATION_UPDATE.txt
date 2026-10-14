P3 RECONCILIATION UPDATE — APPLY INSTRUCTIONS

This is a patch archive. Extract its contents directly into the root of your existing
P3_Network_as_Code_GitOps repository, choosing overwrite/merge when asked. Do not extract
it into another nested P3_Network_as_Code_GitOps folder.

The update aligns selected YAML/template settings with the supplied P1 snapshots and adds
regression tests for the known problems. It also puts the sanitized baseline snapshots under
configs/baseline. Those .cfg files should be ignored by the project's .gitignore and are for
local comparison only; do not force-add them to Git.

After extraction, open the existing project root in VS Code and run these commands in the
PowerShell terminal with the project's .venv activated:

  python scripts/validate_data.py
  python scripts/render_configs.py --mode ci --output build/rendered
  python -m pytest -q

Expected result: data validation passes, then 16 tests pass.

The generated files in build/rendered are CI/reference output using synthetic IPsec keys.
Never deploy or paste them into Packet Tracer. Read docs/BASELINE_RECONCILIATION.md before
considering a candidate for any lab deployment.

This update does not change your running Packet Tracer devices. It only updates local files.
