import argparse
import json
import os
import sys
from pathlib import Path

import qrcode
import questionary
from keyring.errors import KeyringError

from . import Purifier, PurifierError
from .cloud import REGIONS, find_purifiers


def select_region():
    choices = [
        questionary.Choice(f"{name} ({code})", value=code)
        for code, name in REGIONS.items()
    ]
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise PurifierError(
            "For non-interactive region selection, use setup --region CODE. See setup --help."
        )
    return questionary.select(
        "Select your Xiaomi Home region", choices=choices
    ).unsafe_ask()


def display_qr(url, image):
    qr = qrcode.QRCode(border=4)
    qr.add_data(url)
    if image is None:
        print("Scan in Xiaomi Home and approve sign-in.", flush=True)
        qr.print_ascii(invert=True)
    else:
        # A pending login QR is private. Create a new owner-only file even on a shared volume.
        with open(
            image, "xb", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as file:
            qr.make_image().save(file, format="PNG")
        print(f"Scan {image} in Xiaomi Home and approve sign-in.", flush=True)


def setup(args):
    region = args.region or select_region()
    purifiers = find_purifiers(region, lambda url: display_qr(url, args.qr_image))
    if not purifiers:
        raise PurifierError(
            f"No supported 4 Lite with LAN credentials in {REGIONS[region]} ({region}). Check your Xiaomi Home region."
        )
    for purifier in purifiers:
        answer = input(
            f"Read {purifier.model} at {purifier.ip} and save its pairing? [y/N] "
        )
        if answer.strip().lower() in {"y", "yes"}:
            readings = purifier.stats()
            purifier._save()
            print(json.dumps(readings, indent=2))
            return
    raise PurifierError("No purifier selected.")


def main():
    parser = argparse.ArgumentParser(
        description="Read a Xiaomi Smart Air Purifier 4 Lite over Wi-Fi."
    )
    actions = parser.add_subparsers(dest="action")
    actions.add_parser("status", help="print live readings as JSON (default)")
    pair = actions.add_parser("setup", help="pair a purifier through Xiaomi Home")
    regions = ", ".join(f"{code} = {name}" for code, name in REGIONS.items())
    pair.add_argument("--region", choices=REGIONS, help=regions)
    pair.add_argument(
        "--qr-image",
        type=Path,
        metavar="PATH",
        help="write the sign-in QR to a new PNG instead of displaying it in the terminal",
    )
    args = parser.parse_args()
    try:
        if args.action == "setup":
            setup(args)
        else:
            print(json.dumps(Purifier.paired().stats(), indent=2))
    except (KeyboardInterrupt, EOFError):
        parser.exit(130, "Cancelled.\n")
    except (PurifierError, KeyringError, OSError) as exc:
        parser.exit(1, f"purifier-stats: {exc}\n")
