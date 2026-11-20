import base64
import json
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class KnowledgeDownloadHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "knowledge_download_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                observed.update(
                    method=self.command,
                    path=self.path,
                    body=self.rfile.read(int(self.headers.get("Content-Length", "0"))),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    accept=self.headers.get("Accept"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
                if scenario["status"] >= 400:
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                    content_type = "application/json"
                else:
                    payload = base64.b64decode(scenario["content_base64"])
                    content_type = "application/octet-stream"
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", content_type)
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
        service = client.knowledge("workspace-1")
        input_value = scenario["input"]
        call = service.preview_source_file if scenario["operation"] == "preview-source-file" else service.preview_artifact
        try:
            stream = call(input_value["model_id"], input_value["file_id"])
            if scenario["status"] >= 400:
                self.fail("owner error was not raised")
            try:
                self.assertEqual(stream.read(), base64.b64decode(scenario["content_base64"]))
            finally:
                stream.close()
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["body"], b"")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertEqual(observed["accept"], "*/*")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
