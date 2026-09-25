from types import SimpleNamespace

from app.config import (
    AppConfig,
    detect_private_network,
    doctor_report,
    nmap_interface_choices,
    nmap_interface_ipv4,
    resolve_allowed_network,
    resolve_nmap_path,
)


def test_scope_selection_reuses_observation_without_os_commands(monkeypatch):
    def forbidden():
        raise AssertionError("Scope selection must not probe or block the event loop")

    monkeypatch.setattr("app.config.detect_private_network", forbidden)
    assert resolve_allowed_network(AppConfig(), "192.168.0.0/24") == "192.168.0.0/24"
    assert resolve_allowed_network(AppConfig(), "10.240.108.0/22") is None
    assert resolve_allowed_network(AppConfig()) is None


def test_default_config_uses_user_data_dir():
    cfg = AppConfig()
    assert cfg.port == 8765
    assert cfg.max_concurrent_scans == 2
    assert str(cfg.data_dir).endswith("network-assessor")


def test_max_concurrent_scans_uses_a_positive_environment_value(monkeypatch):
    monkeypatch.setenv("APP_MAX_CONCURRENT_SCANS", "3")
    assert AppConfig.from_env().max_concurrent_scans == 3
    monkeypatch.setenv("APP_MAX_CONCURRENT_SCANS", "not-a-number")
    assert AppConfig.from_env().max_concurrent_scans == 2
    monkeypatch.setenv("APP_MAX_CONCURRENT_SCANS", "100")
    assert AppConfig.from_env().max_concurrent_scans == 2


def test_invalid_numeric_environment_values_use_safe_defaults(monkeypatch):
    monkeypatch.setenv("APP_PORT", "not-a-port")
    monkeypatch.setenv("APP_AI_TIMEOUT_SECONDS", "-1")

    config = AppConfig.from_env()

    assert config.port == 8765
    assert config.ai_timeout_s == 60.0


def test_doctor_report_has_expected_fields():
    report = doctor_report()
    assert "python_version" in report
    assert "os" in report
    assert "nmap_available" in report
    assert "provider_configured" in report
    assert isinstance(report["data_dir"], str)


def test_resolve_nmap_path_finds_standard_windows_install(tmp_path, monkeypatch):
    executable = tmp_path / "Nmap" / "nmap.exe"
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path))
    monkeypatch.setattr("app.config.shutil.which", lambda _: None)

    assert resolve_nmap_path(AppConfig()) == str(executable)


def test_detect_private_network_prefers_adapter_with_default_gateway(monkeypatch):
    ipconfig = """
Ethernet adapter Virtual network:

   IPv4 Address. . . . . . . . . . . : 192.168.56.10
   Subnet Mask . . . . . . . . . . . : 255.255.255.0

Wireless LAN adapter Wi-Fi:

   IPv4 Address. . . . . . . . . . . : 192.168.0.24
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.0.1
"""
    monkeypatch.setattr(
        "app.config.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=ipconfig),
    )

    assert detect_private_network() == "192.168.0.0/24"
    assert (
        resolve_allowed_network(AppConfig(allowed_network="192.168.10.0/24")) == "192.168.10.0/24"
    )


def test_nmap_interface_choices_returns_only_active_non_loopback_interfaces(monkeypatch):
    output = """
DEV  (SHORT) IP/MASK          TYPE     UP   MTU  MAC
eth0 (eth0)  192.168.0.2/24  ethernet up   1500 00:00:00:00:00:00
eth1 (eth1)  169.254.1.2/16  ethernet down 1500 00:00:00:00:00:01
lo0  (lo0)   127.0.0.1/8     loopback up   -1
"""
    monkeypatch.setattr("app.config.resolve_nmap_path", lambda config: "nmap")
    monkeypatch.setattr(
        "app.config.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=output),
    )

    assert nmap_interface_choices(AppConfig()) == ["eth0"]


def test_mdns_interface_binding_requires_one_matching_ipv4_address(monkeypatch):
    output = """
eth4 (eth4)  192.168.91.1/24 ethernet up 1500 00:00:00:00:00:01
eth6 (eth6)  192.168.0.216/24 ethernet up 1500 00:00:00:00:00:02
"""
    monkeypatch.setattr("app.config.resolve_nmap_path", lambda config: "nmap")
    monkeypatch.setattr(
        "app.config.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=output),
    )
    assert nmap_interface_ipv4(AppConfig(), "192.168.0.0/24") == "192.168.0.216"
    assert nmap_interface_ipv4(AppConfig(), "192.168.0.0/24", "eth4") is None
