import json
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class SystemHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads(Path("../go-sdk/testdata/system_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                observed.append((self.command, self.path, raw, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), self.headers.get("Authorization"), self.headers.get("Cookie")))
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode()
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        try:
            if scenario["operation"] == "versions":
                result = client.system().versions()
            else:
                result = client.system().webapp_config()
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            message_type = sdk.SystemVersionsResult if scenario["operation"] == "versions" else sdk.WebappConfigResult
            self.assertEqual(result, json_format.ParseDict(scenario["response"]["data"], message_type()))
        self.assertEqual(observed, [(scenario["method"], scenario["path"], b"", "synthetic-key", None, None, None)])


if __name__ == "__main__":
    unittest.main()
