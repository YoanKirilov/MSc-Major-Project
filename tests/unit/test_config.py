from pathlib import Path

from app.config import AppConfig, doctor_report


def test_default_config_uses_user_data_dir():
    cfg = AppConfig()
    assert cfg.port == 8765
    assert cfg.ai_enabled is False
    assert str(cfg.data_dir).endswith("network-assessor")


def test_doctor_report_has_expected_fields():
    report = doctor_report()
    assert "python_version" in report
    assert "os" in report
    assert "nmap_available" in report
    assert "provider_configured" in report
    assert isinstance(report["data_dir"], str)
