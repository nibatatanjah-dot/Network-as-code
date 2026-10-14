# P3 Network Change Assurance Dashboard

This is the client-facing presentation layer for the P3 Network-as-Code project. It explains the network review without requiring a client to read terminal output.

## Open locally

Open `dashboard/index.html` directly in a browser, or serve the repository with any static web server. The dashboard has no build step or external runtime dependency.

## Demonstration flow

1. Start on **Overview** and explain the three-site topology.
2. Open **Safety checks** to show the plain-language security assertions.
3. Open **Change review** and run the safe scenario.
4. Trigger **Unsafe guest rule** to show the review changing to **BLOCKED**.
5. Finish on **Evidence** to explain the 16 passing tests, Batfish result, Git commit, and deployment boundary.

The dashboard deliberately describes the output as a validated design review. It does not claim live device telemetry or deployment to Packet Tracer.
