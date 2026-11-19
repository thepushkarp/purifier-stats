# purifier-stats

Read PM2.5 (µg/m³), temperature (°C), relative humidity (%), remaining filter life (%), power, and mode from a Xiaomi Smart Air Purifier 4 Lite on your Wi-Fi. Supports `zhimi.airp.rmb1` and `zhimi.airpurifier.rma1`.

[Website and interactive sample](https://purifier-stats.thepushkarp.com)

## Install and pair

Requires Python 3.10+ and an OS credential store for saved pairing. On a computer connected to the purifier’s Wi-Fi, run:

```sh
uv tool install --python 3.12 purifier-stats
purifier-stats setup
purifier-stats
```

Select the region shown in Xiaomi Home with ↑/↓ and Enter. Scan the QR in Xiaomi Home, approve sign-in, then confirm the purifier. Setup reads the device before saving its IP, model and token in your credential store. Subsequent reads use the LAN. Run setup again if its address or token changes.

To skip the menu and save a QR image, use `purifier-stats setup --region i2 --qr-image sign-in.png` (India). Use a fresh path and keep setup running while you scan. The file contains a temporary sign-in credential. Remove it after use. See `purifier-stats setup --help` for all regions.

## Python

Install in your virtual environment with `pip install purifier-stats`. After pairing, read the sensors from Python:

```python
from purifier_stats import Purifier

readings = Purifier.paired().stats()
print(readings["pm2_5_ug_m3"])
```

With your own credentials, use `Purifier(ip=ip, token=token, model=model).stats()`. Both interfaces return the same fields. Unavailable sensor values are `None` in Python and `null` in JSON.

## Agent skill

Install the [agent skill](https://github.com/thepushkarp/purifier-stats/blob/main/skills/purifier-stats/SKILL.md) directly from GitHub with the [skills.sh CLI](https://skills.sh/). Select your agent when prompted.

```sh
npx skills add thepushkarp/purifier-stats --skill purifier-stats
```
