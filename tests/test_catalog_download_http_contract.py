import base64
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class CatalogDownloadHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "catalog_download_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}
        content = base64.b64decode(scenario["content_base64"])

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command, path=parsed.path, query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True), body=json.loads(raw) if raw else None,
                    workspace=self.headers.get("X-Workspace-ID"), api_key=self.headers.get("X-API-Key"),
                    accept=self.headers.get("Accept"), authorization=self.headers.get("Authorization"), cookie=self.headers.get("Cookie"),
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            do_GET = do_POST

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        input_value = scenario["input"]
        options = []
        if "as_zip" in input_value:
            options.append(sdk.with_file_as_zip(input_value["as_zip"]))
        service = client.catalog("workspace-1")
        if scenario.get("operation") == "preview-file":
            stream = service.preview_file(input_value["volume_id"], input_value["file_id"])
        elif scenario.get("operation") == "download-table":
            stream = service.download_table(input_value["table_id"])
        elif scenario.get("operation") == "download-workspace-file":
            stream = service.download_workspace_file(input_value["file_id"])
        elif scenario.get("operation") == "preview-workspace-file":
            stream = service.preview_workspace_file(input_value["file_id"])
        elif scenario.get("operation") == "catalog-file-content":
            stream = service.catalog_file_content(input_value["file_id"], input_value["capability"])
        else:
            stream = service.download_file(input_value["volume_id"], input_value["file_id"], *options)
        try:
            self.assertEqual(stream.read(), content)
        finally:
            stream.close()
        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertEqual(observed["accept"], "*/*")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
