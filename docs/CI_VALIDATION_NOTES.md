# Pull Request CI Verification

Date: 2026-10-14

## Initial CI result

The initial main-branch GitHub Actions run completed successfully.

## Automated checks

- YAML linting and network data validation.
- Jinja2 configuration rendering.
- Python unit tests.
- Batfish parsing and network-policy assertions.
- Positive control: HQ Staff HTTPS can reach the HQ server.
- Negative control: HQ Guest HTTPS must not reach the HQ server.
- Negative-test harness: an intentionally unsafe guest-access
  candidate must be rejected by the Batfish policy assertion.

## Important limitation

These checks use generated reference configurations. They do not
prove that the current Packet Tracer devices were automatically
configured, deployed to, or rolled back.

The GitHub Actions run is the authoritative record of execution.
