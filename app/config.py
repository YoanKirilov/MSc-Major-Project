import ipaddress
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_data_dir


def _integer_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if minimum <= value <= maximum else default


def _float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if minimum <= value <= maximum else default


def _pihole_password_from_env() -> tuple[str | None, str | None]:
    """Read one backend-only credential, without putting secrets/paths in errors."""
    password = os.getenv("APP_PIHOLE_PASSWORD") or None
    password_file = os.getenv("APP_PIHOLE_PASSWORD_FILE") or None
    if password and password_file:
        return None, "Set only one of APP_PIHOLE_PASSWORD and APP_PIHOLE_PASSWORD_FILE."
    if password_file:
        try:
            path = Path(password_file).expanduser()
            if not path.is_file():
                return None, "The Pi-hole password file is missing or is not a regular file."
            with path.open("rb") as secret:
                contents = secret.read(4097)
            if len(contents) > 4096:
                return None, "The Pi-hole password file exceeds the 4 KiB limit."
            password = contents.decode("utf-8-sig").rstrip("\r\n")
        except (OSError, ValueError):
            return None, "The Pi-hole password file could not be read as UTF-8."
        if not password:
            return None, "The Pi-hole password file is empty."
    if password and (len(password) > 4096 or any(c in password for c in "\r\n\x00")):
        return None, "The Pi-hole password must be a single line of at most 4096 characters."
    return password, None


@dataclass
class AppConfig:
    data_dir: Path = field(
        default_factory=lambda: Path(user_data_dir("network-assessor", appauthor=False))
    )
    port: int = 8765
    nmap_path: str | None = None
    ai_provider: str = "ollama"
    ai_base_url: str = "http://127.0.0.1:11434"
    ai_model: str = "llama3.2:3b"
    ai_timeout_s: float = 60.0
    allowed_network: str | None = None
    max_concurrent_scans: int = 5
    pihole_url: str | None = None
    pihole_password: str | None = field(default=None, repr=False)
    pihole_configuration_error: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        data_dir = os.getenv("APP_DATA_DIR")
        pihole_password, pihole_error = _pihole_password_from_env()
        return cls(
            data_dir=Path(data_dir)
            if data_dir
            else Path(user_data_dir("network-assessor", appauthor=False)),
            port=_integer_env("APP_PORT", 8765, 1, 65535),
            nmap_path=os.getenv("APP_NMAP_PATH") or None,
            ai_provider=os.getenv("APP_AI_PROVIDER", "ollama").strip().lower(),
            ai_base_url=os.getenv("APP_AI_BASE_URL", "http://127.0.0.1:11434").strip(),
            ai_model=os.getenv("APP_AI_MODEL", "llama3.2:3b").strip(),
            ai_timeout_s=_float_env("APP_AI_TIMEOUT_SECONDS", 60.0, 1.0, 300.0),
            allowed_network=os.getenv("APP_ALLOWED_NETWORK") or None,
            max_concurrent_scans=_integer_env("APP_MAX_CONCURRENT_SCANS", 5, 1, 8),
            pihole_url=os.getenv("APP_PIHOLE_URL") or None,
            pihole_password=pihole_password,
            pihole_configuration_error=pihole_error,
        )


def load_config() -> AppConfig:
    return AppConfig.from_env()


def _is_rfc1918(network: ipaddress.IPv4Network) -> bool:
    return any(
        network.subnet_of(private)
        for private in (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
    )


def _windows_ipv4_gateway(section: str) -> bool:
    """ipconfig can print IPv6 first, then IPv4 on a continuation line."""
    lines = section.splitlines()
    for index, line in enumerate(lines):
        match = re.search(r"Default Gateway[^:]*:[ \t]*(.*)$", line)
        if not match:
            continue
        addresses = [match.group(1).strip()]
        for continuation in lines[index + 1 :]:
            value = continuation.strip()
            if not value or not re.fullmatch(r"[0-9A-Fa-f:.%]+", value):
                break
            addresses.append(value)
        for value in addresses:
            try:
                gateway = ipaddress.ip_address(value.split("%", 1)[0])
            except ValueError:
                continue
            if isinstance(gateway, ipaddress.IPv4Address) and not gateway.is_unspecified:
                return True
    return False


def detect_private_network() -> str | None:
    """Identify the default-route network, not an arbitrary virtual adapter.

    Return its real size; choosing a bounded scan target is a separate decision.
    """
    if os.name == "nt":
        from app.scanner.network import windows_connections

        rows = windows_connections()
        if rows is not None:
            networks = set()
            for row in rows:
                if not any(g and g != "0.0.0.0" for g in (row.get("Gateways") or [])):
                    continue
                for address in row.get("Addresses") or []:
                    try:
                        network = ipaddress.ip_network(
                            f"{address['IPAddress']}/{address['PrefixLength']}", strict=False
                        )
                    except (KeyError, TypeError, ValueError):
                        continue
                    if isinstance(network, ipaddress.IPv4Network) and _is_rfc1918(network):
                        networks.add(str(network))
            return next(iter(networks)) if len(networks) == 1 else None
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=3, check=False
            )
        else:
            result = subprocess.run(
                ["ip", "-o", "-f", "inet", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None

    if os.name != "nt":
        try:
            routes = subprocess.run(
                ["ip", "-4", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        devices = set(re.findall(r"\bdev\s+(\S+)", routes.stdout))
        if routes.returncode != 0 or len(devices) != 1:
            return None
        selected = next(iter(devices))
        for line in result.stdout.splitlines():
            match = re.search(r"^\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", line)
            if not match or match.group(1).split("@")[0] != selected:
                continue
            address, prefix = match.group(2), match.group(3)
            network = ipaddress.ip_network(f"{address}/{prefix}", strict=False)
            if isinstance(network, ipaddress.IPv4Network) and _is_rfc1918(network):
                return str(network)
        return None

    candidates: list[tuple[bool, ipaddress.IPv4Network]] = []
    for section in re.split(r"\r?\n\s*\r?\n", result.stdout):
        address_match = re.search(r"IPv4[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", section)
        mask_match = re.search(r"Subnet Mask[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", section)
        if not address_match or not mask_match:
            continue
        try:
            network = ipaddress.ip_network(
                f"{address_match.group(1)}/{mask_match.group(1)}", strict=False
            )
        except ValueError:
            continue
        if not isinstance(network, ipaddress.IPv4Network) or not _is_rfc1918(network):
            continue
        has_gateway = _windows_ipv4_gateway(section)
        if has_gateway:
            candidates.append((has_gateway, network))
    if not candidates:
        return None
    networks = {str(candidate[1]) for candidate in candidates}
    return next(iter(networks)) if len(networks) == 1 else None


def resolve_allowed_network(config: AppConfig, detected: str | None = None) -> str | None:
    """Choose the scope from an existing observation; never run OS commands here."""
    if config.allowed_network:
        return config.allowed_network
    return detected if detected and ipaddress.ip_network(detected).prefixlen >= 24 else None


def network_warning(scope: str | None, detected: str | None) -> str | None:
    try:
        configured = ipaddress.ip_network(scope, strict=True) if scope else None
        active = ipaddress.ip_network(detected, strict=True) if detected else None
        if configured and not isinstance(configured, ipaddress.IPv4Network):
            raise ValueError("IPv4 scope required")
    except ValueError:
        return "The network range is invalid. Set an authorised private IPv4 range in Settings."
    if not detected:
        return (
            "The active network could not be identified. Confirm your "
            "authorised range and interface in Settings."
        )
    if configured and not configured.subnet_of(active):
        return (
            f"The saved scan range ({scope}) differs from your current network ({detected}). "
            "Open Settings and choose Automatic for this connection, or select the "
            "intended interface and authorised range."
        )
    if not scope:
        return (
            "The active network is larger than the automatic scan limit. "
            "Select an authorised /24 or smaller range in Settings; the app "
            "will not choose another adapter."
        )
    return None


def resolve_nmap_path(config: AppConfig) -> str | None:
    """Return a usable Nmap executable without requiring Windows PATH changes."""
    configured = config.nmap_path
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path)
        on_path = shutil.which(configured)
        if on_path:
            return on_path

    for executable in ("nmap", "nmap.exe"):
        on_path = shutil.which(executable)
        if on_path:
            return on_path

    program_directories = (
        os.getenv("ProgramW6432"),
        os.getenv("ProgramFiles"),
        os.getenv("ProgramFiles(x86)"),
    )
    for directory in dict.fromkeys(directory for directory in program_directories if directory):
        candidate = Path(directory) / "Nmap" / "nmap.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def nmap_preflight(config: AppConfig) -> tuple[bool, str | None]:
    executable = resolve_nmap_path(config)
    if not executable:
        return False, None
    try:
        result = subprocess.run(
            [executable, "-V"], capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False, None
    if result.returncode != 0:
        return False, None
    output = (result.stdout or result.stderr).splitlines()
    return True, output[0].strip() if output else "Nmap"


def nmap_interface_choices(config: AppConfig) -> list[str]:
    executable = resolve_nmap_path(config)
    if not executable:
        return []
    try:
        result = subprocess.run(
            [executable, "--iflist"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    choices = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+\([^)]*\)\s+\S+\s+\S+\s+up\s+", line)
        if match and match.group(1) != "lo0":
            choices.add(match.group(1))
    return sorted(choices)


def nmap_interface_diagnostic(config: AppConfig, scope: str, selected: str | None = None) -> dict:
    """Explain why a single interface can or cannot be bound to this scope."""
    executable = resolve_nmap_path(config)
    if not executable:
        return {"address": None, "reason": "scanner_unavailable"}
    try:
        allowed = ipaddress.ip_network(scope, strict=True)
    except (TypeError, ValueError):
        return {"address": None, "reason": "invalid_scope"}
    if not isinstance(allowed, ipaddress.IPv4Network):
        return {"address": None, "reason": "invalid_scope"}
    try:
        result = subprocess.run([executable, "--iflist"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return {"address": None, "reason": "list_unavailable"}
    if result.returncode != 0:
        return {"address": None, "reason": "list_unavailable"}
    matches = set()
    seen_selected = False
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+\([^)]*\)\s+(\d+\.\d+\.\d+\.\d+)/\d+\s+\S+\s+up\s+", line)
        if not match or (selected and match.group(1) != selected):
            continue
        seen_selected = True
        try:
            address = ipaddress.IPv4Address(match.group(2))
        except ValueError:
            continue
        if address in allowed:
            matches.add((match.group(1), str(address)))
    if len(matches) == 1:
        interface, address = next(iter(matches))
        return {"address": address, "interface": interface, "reason": "ready"}
    reason = (
        "multiple_matches"
        if matches
        else "interface_unavailable"
        if selected and not seen_selected
        else "scope_unmatched"
    )
    return {"address": None, "reason": reason}


def nmap_interface_ipv4(config: AppConfig, scope: str, selected: str | None = None) -> str | None:
    """Find one up interface inside the authorised subnet for interface-bound mDNS."""
    return nmap_interface_diagnostic(config, scope, selected)["address"]


def mdns_interface_message(reason: str, scope: str, detected: str | None) -> str:
    context = f" Scan range: {scope}." + (f" Current network: {detected}." if detected else "")
    messages = {
        "multiple_matches": (
            "More than one connection matches this range. "
            "Choose the intended Interface in Settings."
        ),
        "interface_unavailable": (
            "The saved Interface is no longer available. Open Settings "
            "and choose Automatic or your current connection."
        ),
        "scope_unmatched": (
            "No active connection matches the scan range. "
            "Open Settings and check Network range and Interface."
        ),
        "invalid_scope": "The scan range is invalid. Correct the private IPv4 range in Settings.",
        "list_unavailable": (
            "The scanner could not read your local connections. "
            "Retry, or check the Nmap installation in Settings."
        ),
        "scanner_unavailable": "Nmap is unavailable. Check the scanner installation in Settings.",
    }
    return (
        "Local device announcements could not start. "
        + messages.get(reason, messages["scope_unmatched"])
        + context
    )


def doctor_report() -> dict[str, Any]:
    import sys

    config = load_config()
    nmap_available, nmap_version = nmap_preflight(config)
    return {
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "os": sys.platform,
        "nmap_available": nmap_available,
        "nmap_version": nmap_version,
        "data_dir": str(config.data_dir),
        "provider_configured": config.ai_provider == "ollama" and bool(config.ai_model),
        "ai_provider": config.ai_provider,
    }
