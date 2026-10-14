# Pull Request CI Verification

## Purpose
Demonstrate automated validation of a proposed network change.

## Required checks
- YAML linting and data validation
- Jinja2 configuration rendering
- Python unit tests
- Batfish reachability and security analysis

## Security expectations
- HQ Staff HTTPS to the HQ server should be reachable.
- HQ Guest HTTPS to the HQ server should be blocked.
- An intentionally unsafe guest-access change should fail validation.

## Limitation
These tests use generated reference configurations.
They do not prove that the Packet Tracer devices have been
automatically deployed to or rolled back.
