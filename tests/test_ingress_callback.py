import io
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import moi_product_sdk as sdk


class IngressCallbackContractTest(unittest.TestCase):
    def test_public_transport_and_provider_payload(self):
        client = sdk.Client(
            "http://example.invalid/newmoi",
            sdk.with_api_key("private-key"),
            sdk.with_token("private-token"),
            sdk.with_custom_header("X-Provider-Signature", "provider-signature"),
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"provider-ack"
        with patch("urllib.request.build_opener") as factory:
            wire = factory.return_value.open
            wire.return_value = response
            self.assertEqual(
                b"provider-ack",
                client.verify_ingress_callback("wecom", "ws/1", "ingress/1", {"signature": "valid"}),
            )
            self.assertEqual(
                b"provider-ack",
                client.post_ingress_callback("wecom", "ws/1", "ingress/1", b"<xml/>"),
            )
        self.assertEqual(2, wire.call_count)
        for call in wire.call_args_list:
            request = call.args[0]
            self.assertTrue(request.full_url.startswith("http://example.invalid/newmoi/ingress-callbacks/wecom/ws%2F1/ingress%2F1"))
            headers = {key.lower(): value for key, value in request.header_items()}
            for name in ("x-api-key", "authorization", "cookie", "x-workspace-id"):
                self.assertNotIn(name, headers)
            self.assertEqual("provider-signature", headers["x-provider-signature"])
        self.assertEqual("GET", wire.call_args_list[0].args[0].method)
        self.assertTrue(wire.call_args_list[0].args[0].full_url.endswith("?signature=valid"))
        self.assertEqual("POST", wire.call_args_list[1].args[0].method)
        self.assertEqual(b"<xml/>", wire.call_args_list[1].args[0].data)

    def test_provider_error_is_preserved(self):
        client = sdk.Client("http://example.invalid/newmoi", sdk.with_api_key("private-key"))
        failure = urllib.error.HTTPError(
            "http://example.invalid", 401, "Unauthorized", {},
            io.BytesIO(b'{"code":6,"message":"signature rejected"}'),
        )
        with patch("urllib.request.build_opener") as factory:
            factory.return_value.open.side_effect = failure
            with self.assertRaises(sdk.Error) as raised:
                client.post_ingress_callback("wecom", "workspace", "ingress", b"<xml/>")
        self.assertEqual("6", raised.exception.code)
        self.assertEqual("signature rejected", raised.exception.message)
