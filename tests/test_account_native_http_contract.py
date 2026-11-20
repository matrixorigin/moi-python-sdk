import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AccountNativeHTTPContractTest(unittest.TestCase):
    def test_native_bootstrap_matches_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "account_native_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        current = {}
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                observed.clear()
                observed.update({
                    "method": self.command, "path": urlsplit(self.path).path, "body": raw,
                    "authorization": self.headers.get("Authorization"),
                    "api_key": self.headers.get("X-API-Key"),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "cookie": self.headers.get("Cookie"),
                })
                payload = json.dumps(current["response"]).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_token("native-token"))
        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                result = client.account().bootstrap_native()
                expected = json_format.ParseDict(scenario["response"]["data"], sdk.NativeBootstrapResult())
                self.assertEqual(result, expected)
                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["body"], b"")
                self.assertEqual(observed["authorization"], "Bearer native-token")
                self.assertIsNone(observed["api_key"])
                self.assertIsNone(observed["workspace"])
                self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
