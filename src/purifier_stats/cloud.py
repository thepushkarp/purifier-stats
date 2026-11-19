"""Xiaomi Home QR sign-in and device lookup for one setup session."""

import base64
import json
import os
import time

import requests
from micloud import miutils

from . import MODELS, Purifier, PurifierError

REGIONS = {
    "cn": "Chinese mainland",
    "de": "Europe (Germany)",
    "i2": "India",
    "in": "India (alternate server)",
    "ru": "Russia",
    "sg": "Singapore",
    "tw": "Taiwan",
    "us": "United States",
}


def _account_data(response):
    response.raise_for_status()
    return json.loads(response.text.removeprefix("&&&START&&&"))


def _sign_in(session, display_qr):
    params = {
        "_qrsize": 480,
        "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
        "callback": "https://sts.api.io.mi.com/sts",
        "sid": "xiaomiio",
        "_hasLogo": "false",
        "serviceParam": "",
        "_locale": "en_GB",
        "_dc": int(time.time() * 1000),
    }
    qr = _account_data(
        session.get(
            "https://account.xiaomi.com/longPolling/loginUrl", params=params, timeout=15
        )
    )
    display_qr(qr["loginUrl"])
    deadline = time.monotonic() + int(qr["timeout"])
    while (remaining := deadline - time.monotonic()) > 0:
        try:
            login = _account_data(session.get(qr["lp"], timeout=min(10, remaining)))
            break
        except requests.ReadTimeout:
            continue
    else:
        raise PurifierError("QR sign-in expired. Run setup again for a new code.")
    response = session.get(login["location"], timeout=15)
    response.raise_for_status()
    return login["userId"], login["ssecurity"], response.cookies["serviceToken"]


def _list_purifiers(session, region, user_id, secret, service_token):
    host = "api.io.mi.com" if region == "cn" else f"{region}.api.io.mi.com"
    cookies = {
        "userId": str(user_id),
        "serviceToken": service_token,
        "yetAnotherServiceToken": service_token,
        "locale": "en_GB",
        "timezone": "GMT+00:00",
        "is_daylight": "0",
        "dst_offset": "0",
        "channel": "MI_APP_STORE",
    }
    headers = {
        "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
        "Accept-Encoding": "identity",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def query(path, payload):
        url = f"https://{host}/app{path}"
        # The signed nonce ends with the current UTC minute in four big-endian bytes.
        nonce = base64.b64encode(
            os.urandom(8) + (int(time.time()) // 60).to_bytes(4, "big")
        ).decode()
        signed = miutils.signed_nonce(secret, nonce)
        params = miutils.generate_enc_params(
            url, "POST", signed, nonce, {"data": json.dumps(payload)}, secret
        )
        response = session.post(
            url, params=params, cookies=cookies, headers=headers, timeout=15
        )
        response.raise_for_status()
        data = json.loads(miutils.decrypt_rc4(signed, response.text))
        if data.get("code", 0) != 0:
            raise PurifierError(
                f"Xiaomi Home returned code {data['code']} for {path} in region {region}."
            )
        return data["result"]

    homes = query(
        "/v2/homeroom/gethome",
        {
            "fg": True,
            "fetch_share": True,
            "fetch_share_dev": True,
            "limit": 300,
            "app_ver": 7,
        },
    )
    owners = {(h["id"], user_id) for h in homes.get("homelist") or []}
    shared = query("/v2/user/get_device_cnt", {"fetch_own": True, "fetch_share": True})
    owners.update(
        (h["home_id"], h["home_owner"])
        for h in (shared.get("share") or {}).get("share_family") or []
    )
    devices = {}
    for home, owner in owners:
        items = query(
            "/v2/home/home_device_list",
            {
                "home_owner": int(owner),
                "home_id": int(home),
                "limit": 200,
                "get_split_device": True,
                "support_smart_home": True,
            },
        )
        for item in items.get("device_info") or []:
            if (
                item.get("model") in MODELS
                and item.get("localip")
                and item.get("token")
            ):
                devices[item["did"]] = Purifier(
                    item["localip"], item["token"], item["model"]
                )
    return list(devices.values())


def find_purifiers(region, display_qr):
    if region not in REGIONS:
        raise ValueError("Unknown Xiaomi Home region.")
    with requests.Session() as session:
        operation = "complete Xiaomi Home QR sign-in"
        try:
            credentials = _sign_in(session, display_qr)
            operation = "list paired purifiers"
            return _list_purifiers(session, region, *credentials)
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            # Request exceptions may include session credentials in the URL.
            raise PurifierError(
                f"Unable to {operation} for server {region} ({type(exc).__name__})."
            ) from None
