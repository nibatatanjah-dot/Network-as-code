# P3 Network Change Assurance Dashboard

This is the client-facing presentation layer for the P3 Network-as-Code project. It explains the validated network model without requiring a client to read terminal output.

## Open locally

Open `dashboard/index.html` directly in a browser, or serve the repository with any static web server. The dashboard has no build step or external runtime dependency.

## Demonstration flow

1. Start on **Overview** and explain the three-site topology.
2. Open **Policy gate** to show the plain-language security assertions.
3. Open **Change simulator** and run the safe scenario.
4. Trigger **Unsafe guest rule** to show the security gate changing to **BLOCKED**.
5. Finish on **Evidence** to explain the 16 passing tests, Batfish result, Git commit, and deployment boundary.

The dashboard deliberately labels the output as a validated reference candidate. It does not claim live device telemetry or deployment to Packet Tracer.
