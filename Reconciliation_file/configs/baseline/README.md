# Sanitized P1 baseline snapshots

These seven `.cfg` files are sanitized observations copied from the user's supplied `show running-config` output. They are for read-only comparison, not deployment. Credentials/hashes and device serial identifiers have been removed.

The `.gitignore` intentionally ignores `configs/baseline/*.cfg`, so these local baselines should remain untracked by default. Keep unredacted originals outside this project in a secured folder. Never paste these reference snapshots directly into Packet Tracer devices.

Generated reference candidates live in `build/rendered/`; they are a desired-state model and intentionally differ where the model corrects identified defects or adds policy controls. Review `docs/BASELINE_RECONCILIATION.md` before using any candidate.
