from __future__ import annotations

import ipaddress

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, iso_z, utc_now


class Settings(StrictModel):
    schema_version: int = 1
    revision: int = 1
    allowed_network: str | None = None
    interface: str | None = Field(default=None, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    profile_id: str = "tcp12-udp3-v5"
    retain_raw_xml: bool = False
    mdns_enabled: bool = False
    ai_enabled: bool = False
    ai_consent_revision: int = 0
    updated_at: str | None = Field(default_factory=lambda: iso_z(utc_now()))

    @field_validator("allowed_network")
    @classmethod
    def validate_allowed_network(cls, value: str | None):
        if value is None:
            return None
        try:
            network = ipaddress.ip_network(value, strict=True)
        except ValueError as exc:
            raise ValueError("allowed network must be canonical IPv4 CIDR") from exc
        private_networks = tuple(
            ipaddress.ip_network(cidr)
            for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
        )
        if (
            not isinstance(network, ipaddress.IPv4Network)
            or network.prefixlen < 24
            or not any(network.subnet_of(private) for private in private_networks)
        ):
            raise ValueError("allowed network must be an RFC1918 IPv4 /24 or smaller scope")
        return str(network)


class SettingsUpdate(StrictModel):
    expected_revision: int
    allowed_network: str | None = None
    interface: str | None = Field(default=None, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    retain_raw_xml: bool | None = None
    mdns_enabled: bool | None = None
    ai_enabled: bool | None = None

    _validate_allowed_network = field_validator("allowed_network")(
        Settings.validate_allowed_network.__func__
    )

    @model_validator(mode="after")
    def reject_null_boolean_updates(self):
        for field in ("retain_raw_xml", "mdns_enabled", "ai_enabled"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} must be true or false")
        return self
