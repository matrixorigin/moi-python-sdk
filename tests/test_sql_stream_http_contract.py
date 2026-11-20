import base64
import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class SQLStreamHTTPContractTest(unittest.TestCase):
    def test_download_and_preview_preserve_raw_bytes(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "sql_stream_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        current = {}
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def receive(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                observed.clear()
                observed.update({
                    "method": self.command, "path": urlsplit(self.path).path,
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "body": json.loads(body) if body else None,
                })
                payload = base64.b64decode(current["response_base64"])
                self.send_response(current["status"])
                self.send_header("Content-Type", current["response_content_type"])
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = receive
            do_POST = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                if scenario["operation"] == "download-query-result":
                    stream = client.sql("workspace-1").download_query_result(scenario["statement_id"])
                else:
                    stream = client.agents("workspace-1").preview_query_visual(scenario["agent_id"], scenario["file_id"])
                try:
                    self.assertEqual(stream.read(), base64.b64decode(scenario["response_base64"]))
                finally:
                    stream.close()
                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertEqual(observed["api_key"], "synthetic-key")
                self.assertEqual(observed["body"], scenario["request"])


if __name__ == "__main__":
    unittest.main()
