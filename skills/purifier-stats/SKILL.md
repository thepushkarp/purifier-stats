---
name: purifier-stats
description: Read live Xiaomi Smart Air Purifier 4 Lite sensors over local Wi-Fi, or pair the purifier with Xiaomi Home for future readings.
---

Run `purifier-stats` on a machine on the purifier’s LAN. It reads the saved pairing and prints JSON. Report PM2.5 in µg/m³, temperature in °C, humidity and remaining filter life in percent. Treat null as unavailable.

If the CLI is missing, install it from PyPI with `uv tool install --python 3.12 purifier-stats`.

For first pairing, run `purifier-stats setup` in an interactive terminal. Select the region configured in Xiaomi Home. For a local image handoff, use `purifier-stats setup --region CODE --qr-image PATH` with a fresh private path; region codes are listed by `purifier-stats setup --help`. Keep the process running, show the user the image locally, and let them approve sign-in on their phone. Confirm the intended device before saving. The CLI retrieves its token directly into the OS credential store. Keep login images, URLs, and tokens out of logs and shared messages.
