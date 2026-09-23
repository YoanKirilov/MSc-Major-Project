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


@dataclass
class AppConfig:
    data_dir: Path = field(default_factory=lambda: Path(user_data_dir("network-assessor", appauthor=False)))
    port: int = 8765
    nmap_path: str | None = None
    ai_provider: str = "ollama"
    ai_base_url: str = "http://127.0.0.1:11434"
    ai_model: str = "llama3.2:3b"
    ai_timeout_s: float = 60.0
    allowed_network: str | None = None
    max_concurrent_scans: int = 2

    @classmethod
    def from_env(cls) -> "AppConfig":
        data_dir = os.getenv("APP_DATA_DIR")
        return cls(
            data_dir=Path(data_dir) if data_dir else Path(user_data_dir("network-assessor", appauthor=False)),
            port=_integer_env("APP_PORT", 8765, 1, 65535),
            nmap_path=os.getenv("APP_NMAP_PATH") or None,
            ai_provider=os.getenv("APP_AI_PROVIDER", "ollama").strip().lower(),
            ai_base_url=os.getenv("APP_AI_BASE_URL", "http://127.0.0.1:11434").strip(),
            ai_model=os.getenv("APP_AI_MODEL", "llama3.2:3b").strip(),
            ai_timeout_s=_float_env("APP_AI_TIMEOUT_SECONDS", 60.0, 1.0, 300.0),
            allowed_network=os.getenv("APP_ALLOWED_NETWORK") or None,
            max_concurrent_scans=_integer_env("APP_MAX_CONCURRENT_SCANS", 2, 1, 8),
        )


def load_config() -> AppConfig:
    return AppConfig.from_env()


def _is_rfc1918(network: ipaddress.IPv4Network) -> bool:
    return any(network.subnet_of(private) for private in (
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
    ))


def detect_private_network() -> str | None:
    """Find an active RFC1918 IPv4 subnet suitable for the bounded Light scan."""
    try:
        if os.name == "nt":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=3, check=False)
        else:
            result = subprocess.run(["ip", "-o", "-f", "inet", "addr", "show"], capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None

    if os.name != "nt":
        for address, prefix in re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", result.stdout):
            network = ipaddress.ip_network(f"{address}/{prefix}", strict=False)
            if isinstance(network, ipaddress.IPv4Network) and network.prefixlen >= 24 and _is_rfc1918(network):
                return str(network)
        return None

    candidates: list[tuple[bool, ipaddress.IPv4Network]] = []
    for section in re.split(r"\r?\n\s*\r?\n", result.stdout):
        address_match = re.search(r"IPv4[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", section)
        mask_match = re.search(r"Subnet Mask[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", section)
        if not address_match or not mask_match:
            continue
        try:
            network = ipaddress.ip_network(f"{address_match.group(1)}/{mask_match.group(1)}", strict=False)
        except ValueError:
            continue
        if not isinstance(network, ipaddress.IPv4Network) or network.prefixlen < 24 or not _is_rfc1918(network):
            continue
        has_gateway = bool(re.search(r"Default Gateway[^:]*:\s*\d+\.\d+\.\d+\.\d+", section))
        candidates.append((has_gateway, network))
    if not candidates:
        return None
    candidates.sort(key=lambda candidate: not candidate[0])
    return str(candidates[0][1])


def resolve_allowed_network(config: AppConfig) -> str | None:
    return config.allowed_network or detect_private_network()


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
        result = subprocess.run([executable, "-V"], capture_output=True, text=True, timeout=3, check=False)
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


def nmap_interface_ipv4(config: AppConfig, scope: str, selected: str | None = None) -> str | None:
    """Find one up interface inside the authorised subnet for interface-bound mDNS."""
    executable = resolve_nmap_path(config)
    if not executable:
        return None
    try:
        allowed = ipaddress.ip_network(scope, strict=True)
        result = subprocess.run([executable, "--iflist"], capture_output=True, text=True, timeout=5)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not isinstance(allowed, ipaddress.IPv4Network):
        return None
    matches = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+\([^)]*\)\s+(\d+\.\d+\.\d+\.\d+)/\d+\s+\S+\s+up\s+", line)
        if not match or (selected and match.group(1) != selected):
            continue
        try:
            address = ipaddress.IPv4Address(match.group(2))
        except ValueError:
            continue
        if address in allowed:
            matches.add(str(address))
    return next(iter(matches)) if len(matches) == 1 else None


def doctor_report() -> dict[str, Any]:
    import sys

    config = load_config()
    nmap_available, nmap_version = nmap_preflight(config)
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "os": sys.platform,
        "nmap_available": nmap_available,
        "nmap_version": nmap_version,
        "data_dir": str(config.data_dir),
        "provider_configured": config.ai_provider == "ollama" and bool(config.ai_model),
        "ai_provider": config.ai_provider,
    }
