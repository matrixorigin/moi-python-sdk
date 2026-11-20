import base64
import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentPackageHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_package_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                parsed = urllib.parse.urlsplit(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    body=raw,
                    accept=self.headers.get("Accept"),
                    content_type=self.headers.get("Content-Type"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    runtime_authorization=self.headers.get("Runtime-Authorization"),
                )
                if "response_base64" in scenario:
                    payload = base64.b64decode(scenario["response_base64"])
                else:
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                headers = dict(scenario.get("response_headers", {}))
                headers.setdefault("Content-Type", "application/json")
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace-1")
        operation = scenario["operation"]
        file = base64.b64decode(scenario.get("file_base64", ""))
        stream = None
        try:
            if operation == "load-agent-package":
                result = service.load_agent_package(file)
            elif operation == "export-agent-package":
                stream = service.export_agent_package(scenario["agent_id"], scenario["version"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            response = scenario["response"]
            self.assertEqual(error.code, str(response["code"]))
            self.assertEqual(error.message, response.get("msg", response.get("message")))
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
            self.assertEqual(error.details, response.get("details", {}))
        else:
            self.assertLess(scenario["status"], 400)
            if operation == "load-agent-package":
                self.assertEqual(result, scenario["response"]["data"])

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertIsNone(observed["runtime_authorization"])
        if operation == "load-agent-package":
            self.assertEqual(observed["content_type"], "application/vnd.moi.agent+zip")
            self.assertEqual(observed["accept"], "application/json")
            self.assertEqual(observed["body"], file)
        else:
            self.assertEqual(observed["accept"], "*/*")
            self.assertEqual(observed["body"], b"")
        if stream is not None:
            try:
                self.assertEqual(stream.status, scenario["status"])
                self.assertEqual(stream.read(), base64.b64decode(scenario["response_base64"]))
                for key, value in scenario.get("response_headers", {}).items():
                    self.assertEqual(stream.headers.get(key), value)
            finally:
                stream.close()


if __name__ == "__main__":
    unittest.main()
