# Pi-hole setup — prepared, not activated

Implementation-only update, 25 September 2026. No container, DNS service, scan or test
was started. No router settings, credentials or existing reports were changed.
The new configuration and regression tests have **not been executed**.

## What this adds

Pi-hole remains a separate, optional service. NetGuard reads its v6 device-name data;
it does not install Pi-hole inside Python, configure your router or replace Nmap.
The deployment template pins the official
[2026.09.0 image](https://github.com/pi-hole/docker-pi-hole/releases/tag/2026.09.0).
Recheck its security updates before a later deployment; a version pin is not an
automatic update policy.

The base Compose file publishes only `127.0.0.1:8081` for the web interface/API.
DHCP and NTP serving are disabled; there are no additional capabilities, host networking
or automatic restarts. DNS port 53 is published only by the separate home-network file.
Starting Pi-hole later can download lists and contact external services; loopback-only
published ports do not make the container an offline environment.
The template forwards DNS to `1.1.1.1` and `1.0.0.1` by default; set `PIHOLE_UPSTREAMS`
to your chosen semicolon-separated resolver addresses before deployment if needed.

NetGuard can read a UTF-8 password file through `APP_PIHOLE_PASSWORD_FILE`. It does not
return the password or its file path in Settings/status responses, save it in reports,
or connect to Pi-hole merely to display setup status. Missing/invalid configuration is
reported without preventing access to the rest of the app.

## Choose the host at home

- **Existing Pi-hole v6:** use its private IP origin and a dedicated application password.
  No Docker setup is needed. Prefer HTTPS with a trusted certificate valid for that IP;
  NetGuard intentionally does not bypass certificate validation or accept DNS hostnames.
- **For useful home device names:** a Raspberry Pi or supported Linux home server, or a
  carefully configured Linux VM on the home LAN, is generally a better fit than a laptop
  container. It must actually have relevant client/name records. Use the
  [official installation instructions](https://docs.pi-hole.net/main/basic-install/).
- **For local integration/development:** the provided Docker template is an option.
  Windows requires a Linux-container runtime (for example Docker Desktop with WSL2).
  This work did not install Docker/WSL, create a VM or enable Windows features.

Do not deploy or expose DNS on the current shared network. Being connected is not
authorisation. The commands below are for later, on your own authorised network.

## 1. Start a local Pi-hole later (optional Docker path)

Use two different secrets: an administrator password for Pi-hole itself, and a Pi-hole
application password for NetGuard. Create each as a private, single-line UTF-8 file
outside this repository and outside OneDrive. Restrict access to your account; on Linux
use file mode `600`. Git ignore rules are not encryption or access controls.

First create a **strong, nonempty administrator password** in the administrator file.
Do not create an empty file or use a sample password: Pi-hole can disable authentication
with an empty password. Set its absolute path (not its contents) in PowerShell:

```powershell
$env:PIHOLE_ADMIN_PASSWORD_FILE = Read-Host 'Absolute path to the private administrator-password file'
docker compose -f deployment/pihole/compose.yaml up -d
```

Run from the project root. Docker reads the password using its file-backed secret
mechanism, following the [Pi-hole Docker configuration](https://docs.pi-hole.net/docker/configuration/).
The secret is not encrypted by Compose; protect the source file and Docker access.
On Linux use `export PIHOLE_ADMIN_PASSWORD_FILE=/absolute/private/path` instead of the
PowerShell assignment, and the same Compose command.

On the same host, open `http://127.0.0.1:8081/admin/`. In Pi-hole's Settings, generate an
application password and save it in the second private file. Do not enable elevated
application-password permissions just for name imports. Pi-hole documents this
[application-password authentication](https://docs.pi-hole.net/api/auth/).

## 2. Connect NetGuard later

Stop the existing backend task first; only one instance may use the saved-data folder.
In VS Code, choose **Terminal > Run Task > NetGuard: Start backend with Pi-hole**.
Enter the origin (`http://127.0.0.1:8081` for the local container) and the **absolute file
path** to the application password. Do not paste the password into the task prompt.
The task does not launch Pi-hole or start a scan and does not run automatically.

Alternatively, from the project root in PowerShell:

```powershell
$env:APP_PIHOLE_URL = 'http://127.0.0.1:8081'
$env:APP_PIHOLE_PASSWORD = ''
$env:APP_PIHOLE_PASSWORD_FILE = Read-Host 'Absolute path to the private application-password file'
.\.venv\Scripts\python.exe -m app serve --port 8765
```

Set only one password source. Files are limited to 4 KiB; a UTF-8 BOM and trailing
newlines are accepted. Empty files, invalid encoding and embedded newlines are rejected.
Credentials are read on startup; restart the backend after rotation. The normal backend
task does not remember settings entered into the Pi-hole-specific task, and the app
still does not automatically read `.env` files.

At home, enable **Use names from my Pi-hole** in NetGuard Settings. "Configured" means
the details were accepted locally, not that login or name extraction succeeded. Requests
occur only during an explicitly started, authorised scan with the option enabled. The
connector authenticates, reads `/api/network/devices` and `/api/dhcp/leases`, then logs
out. It does not change filtering, DNS or DHCP settings.

## 3. Give Pi-hole relevant home data (separate, deliberate step)

A newly started container can have no useful names. Installing Pi-hole alone does not
make it see every connected device. For a small trial, use a single device you own as a
DNS client, after confirming the host's private home address and firewall/port settings.
Do not change router-wide DNS or disable the router's DHCP server as part of this setup.

The optional home Compose file publishes TCP/UDP port 53 on one explicitly supplied host
address. Never supply `0.0.0.0`, a public address or a shared-network interface:

```powershell
$env:PIHOLE_HOME_IP = Read-Host 'This Pi-hole host computer private IPv4 address on your authorised home LAN'
docker compose -f deployment/pihole/compose.yaml -f deployment/pihole/compose.home.yaml up -d
```

Keep `PIHOLE_ADMIN_PASSWORD_FILE` set as above. The address is the Pi-hole **host's**
address, not the router address or a CIDR range. The admin/API port remains loopback-only;
this profile assumes NetGuard runs on the same host. A remote Pi-hole deployment needs
separately reviewed admin access/TLS/firewall configuration. Do not expose the admin
port to the internet. No firewall rules are installed by these files.

DNS queries alone may not provide hostnames. Router reverse DNS/conditional forwarding
can help where supported, but requires the actual home router and domain settings.
Router-only forwarding and Docker/VM NAT may hide individual client addresses or MACs.
For networking tradeoffs see [Pi-hole Docker networking](https://docs.pi-hole.net/docker/dhcp/).
This is why the container path is not a promise of complete naming.

Pi-hole DHCP leases are absent when Pi-hole is not your DHCP server (as in these files).
NetGuard ignores expired leases and requires a matching observed MAC for historical
network-table names. If Docker does not preserve a suitable MAC association, that name
will intentionally not be imported. NetGuard will retain other name sources or show an
unknown name instead of guessing. Names never establish reachability or safety.

## Data, stopping and rollback

Pi-hole state is in the Docker named volume `netguard-pihole_pihole-data`, separate from
NetGuard JSON. Pi-hole has its own internal databases; NetGuard has **not** migrated to
SQLite. Pi-hole may retain DNS activity and device identifiers: keep its backups private.

Before leaving home or shutting down the DNS host, restore any test device's previous
DNS configuration so it does not lose name resolution. Turn off Pi-hole names in NetGuard
and stop the container:

```powershell
docker compose -f deployment/pihole/compose.yaml stop
```

This retains the named volume. Do not use `down -v` unless intentionally deleting
Pi-hole data. To remove the home port bindings on a later local-only restart, recreate
the service using the base file alone. It does not auto-start on the next boot.

## Deferred acceptance checklist

No items in this checklist were run for this implementation:

1. Install the updated pinned dependencies in an isolated environment and run offline
   tests, including `tests/unit/test_pihole_setup.py`, then browser/package checks.
2. Validate Compose configuration and start Pi-hole at home; confirm authentication is
   required and only intended ports/interfaces are exposed.
3. Check Pi-hole's actual network/lease records for one authorised device. Record whether
   name, IP, MAC and timestamps exist before expecting NetGuard to import them.
4. Run an authorised single-device scan with isolated `APP_DATA_DIR`; compare imported
   names/provenance with Pi-hole. Exercise no-name, expired lease, mismatched MAC and
   unavailable-Pi-hole cases. Save anonymised evidence, not credentials.
5. Confirm the scan remains honest and readable with and without imported names and
   Ollama output. Old reports can be prepared with Ollama from their existing report
   action; they were not automatically rewritten by this work.
