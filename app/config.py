import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_data_dir


@dataclass
class AppConfig:
    data_dir: Path = field(default_factory=lambda: Path(user_data_dir("network-assessor", appauthor=False)))
    port: int = 8765
    nmap_path: str | None = None
    ai_model: str | None = None
    ai_enabled: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        data_dir = os.getenv("APP_DATA_DIR")
        port_value = os.getenv("APP_PORT", "8765")
        port = int(port_value)
        return cls(
            data_dir=Path(data_dir) if data_dir else Path(user_data_dir("network-assessor", appauthor=False)),
            port=port,
            nmap_path=os.getenv("APP_NMAP_PATH") or None,
            ai_model=os.getenv("APP_AI_MODEL") or None,
            ai_enabled=bool(os.getenv("AI_ENABLED") or False),
        )


def load_config() -> AppConfig:
    return AppConfig.from_env()


def doctor_report() -> dict[str, Any]:
    import shutil
    import sys

    nmap_path = shutil.which("nmap")
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "os": sys.platform,
        "nmap_available": bool(nmap_path),
        "nmap_version": None,
        "data_dir": str(Path(user_data_dir("network-assessor", appauthor=False))),
        "provider_configured": bool(os.getenv("OPENAI_API_KEY")),
    }
