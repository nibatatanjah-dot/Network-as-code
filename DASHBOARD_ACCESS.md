# P3 Network Assurance Dashboard

## Local dashboard

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\start-dashboard.ps1" -Port 8000
```

Open this address:

```text
http://localhost:8000/?v=d5a763d
```

If the terminal is currently inside the `dashboard` folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File "..\start-dashboard.ps1" -Port 8000
```

## Hosted dashboard

Open:

```text
https://p3-network-change-assurance.nutmegpine1.chatgpt.site/?v=d5a763d
```

The hosted dashboard is private and requires the authorized account.

## Interactive demonstration controls

- **Run safe scenario**: opens the safe change review.
- **Run policy gate**: confirms the four policy checks.
- **Test unsafe change**: demonstrates the blocked scenario and returns `EXIT 1`.
- **Copy summary**: copies the plain-language result for a client briefing.
- **Network nodes**: open details for each modeled device.
- **Overview / Safety checks / Change review / Proof**: switch between dashboard sections.

## If the page shows 404

Stop the old server with `Ctrl+C`, then restart it using the launcher above. Do not run:

```powershell
.\P3_Network_as_Code_GitOps\start-dashboard.ps1
```

while already inside the `dashboard` folder. From that folder, the correct path is:

```powershell
..\start-dashboard.ps1
```

## If port 8000 is already in use

Use another port:

```powershell
powershell -ExecutionPolicy Bypass -File ".\start-dashboard.ps1" -Port 8001
```

Then open:

```text
http://localhost:8001/?v=d5a763d
```

## Browser refresh

If an old version appears, close the old dashboard tab and press `Ctrl+F5` after opening the address above.
