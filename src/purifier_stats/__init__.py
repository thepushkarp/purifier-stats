"""Local sensor readings for the Xiaomi Smart Air Purifier 4 Lite."""

import ipaddress
import json
import re
from dataclasses import asdict, dataclass, field

import keyring
from miio import AirPurifierMiot
from miio.exceptions import DeviceException

MODELS = {"zhimi.airp.rmb1", "zhimi.airpurifier.rma1"}
_SERVICE = "Xiaomi Purifier Stats"
_ACCOUNT = "purifier"


class PurifierError(RuntimeError):
    """The purifier could not be paired or read."""


@dataclass(frozen=True)
class Purifier:
    ip: str
    token: str = field(repr=False)
    model: str

    def __post_init__(self):
        ipaddress.IPv4Address(self.ip)
        if self.model not in MODELS:
            raise ValueError(f"Unsupported purifier model: {self.model}")
        if not re.fullmatch(r"[0-9a-fA-F]{32}", self.token):
            raise ValueError("The device token must contain 32 hexadecimal characters.")

    @classmethod
    def paired(cls):
        """Load the purifier selected by the setup command."""
        saved = keyring.get_password(_SERVICE, _ACCOUNT)
        if saved is None:
            raise PurifierError("No paired purifier. Run purifier-stats setup.")
        try:
            return cls(**json.loads(saved))
        except (TypeError, ValueError) as exc:
            raise PurifierError(
                "Invalid saved pairing. Run purifier-stats setup."
            ) from exc

    def _save(self):
        keyring.set_password(_SERVICE, _ACCOUNT, json.dumps(asdict(self)))

    def stats(self) -> dict:
        """Read the current operating state and sensor values over the LAN."""
        try:
            status = AirPurifierMiot(self.ip, self.token, model=self.model).status()
            return {
                "ip": self.ip,
                "model": self.model,
                "power": status.power,
                "mode": status.mode.name,
                "pm2_5_ug_m3": status.aqi,
                "temperature_c": status.temperature,
                "humidity_percent": status.humidity,
                "filter_life_percent": status.filter_life_remaining,
            }
        except (DeviceException, OSError, KeyError) as exc:
            raise PurifierError(
                f"Could not read purifier at {self.ip}. Check Wi-Fi or run purifier-stats setup to refresh pairing."
            ) from exc
