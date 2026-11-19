import json
import stat
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from micloud import miutils
from PIL import Image

from purifier_stats import PurifierError
from purifier_stats.cli import display_qr, setup
from purifier_stats.cloud import find_purifiers


class PairingTests(unittest.TestCase):
    def test_qr_export_preserves_existing_file_and_terminal_output(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            redirect_stdout(StringIO()) as output,
        ):
            path = Path(directory) / "login.png"
            display_qr("https://example.org/test", path)
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                image.verify()
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                display_qr("second", path)
            display_qr("https://example.org/test", None)
            self.assertGreater(len(output.getvalue().splitlines()), 10)

    def test_approved_shared_home_returns_only_supported_purifier(self):
        session = Mock()
        secret = "Zml4dHVyZQ=="
        device = {
            "did": "fixture",
            "token": "ab" * 16,
            "localip": "192.0.2.1",
            "model": "zhimi.airp.rmb1",
        }
        session.get.side_effect = [
            Mock(text='&&&START&&&{"loginUrl":"scan","lp":"poll","timeout":60}'),
            requests.ReadTimeout(),
            Mock(
                text=json.dumps(
                    {"userId": "1", "location": "exchange", "ssecurity": secret}
                )
            ),
            Mock(cookies={"serviceToken": "fixture"}),
        ]

        def cloud_response(url, *, params, **kwargs):
            key = miutils.signed_nonce(secret, params["_nonce"])
            body = json.loads(miutils.decrypt_rc4(key, params["data"]))
            if url.endswith("/gethome"):
                result = {"homelist": []}
            elif url.endswith("/get_device_cnt"):
                result = {"share": {"share_family": [{"home_id": 2, "home_owner": 3}]}}
            else:
                self.assertEqual((body["home_id"], body["home_owner"]), (2, 3))
                result = {"device_info": [{"model": "unrelated"}, device]}
            self.assertTrue(url.startswith("https://i2.api.io.mi.com/"))
            return Mock(text=miutils.encrypt_rc4(key, json.dumps({"result": result})))

        session.post.side_effect = cloud_response
        display = Mock()
        with patch("requests.Session") as factory:
            factory.return_value.__enter__.return_value = session
            found = find_purifiers("i2", display)
        display.assert_called_once_with("scan")
        self.assertEqual([p.ip for p in found], ["192.0.2.1"])
        self.assertNotIn(device["token"], repr(found))

    def test_unreachable_replacement_preserves_saved_pairing(self):
        with (
            patch("purifier_stats.cli.find_purifiers") as lookup,
            patch("builtins.input", return_value="y"),
            patch("keyring.set_password") as save,
        ):
            device = Mock()
            device.stats.side_effect = PurifierError("unreachable")
            lookup.return_value = [device]
            with self.assertRaisesRegex(PurifierError, "unreachable"):
                setup(Namespace(region="i2", qr_image=None))
            save.assert_not_called()
            device._save.assert_not_called()
