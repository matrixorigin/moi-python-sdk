import base64
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class WebappPublicFileHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads(Path("../go-sdk/testdata/webapp_public_file_http_contract.json").read_text())
        for scenario in cases:
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
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=raw,
                    content_type=self.headers.get("Content-Type"),
                    accept=self.headers.get("Accept"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    role=self.headers.get("X-MOI-Role-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    runtime=self.headers.get("X-MOI-Runtime-Authorization"),
                    probe=self.headers.get("X-Webapp-Probe"),
                )
                if scenario.get("response_base64"):
                    payload = base64.b64decode(scenario["response_base64"])
                else:
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode()
                self.send_response(scenario["status"])
                self.send_header("Content-Type", scenario.get("response_content_type", "application/json"))
                for key, value in scenario.get("response_headers", {}).items():
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
        client = sdk.Client(
            f"http://127.0.0.1:{server.server_port}/newmoi",
            sdk.with_api_key("private-key"), sdk.with_token("private-token"), sdk.with_session_cookie("private-cookie"),
            sdk.with_runtime_authorization("private-runtime-grant"), sdk.with_workspace_current_role_id("workspace-1", "7"),
            sdk.with_custom_header("X-Webapp-Probe", "preserved"),
        )
        opts = tuple(sdk.with_query_values(key, *values) for key, values in sorted(scenario["query"].items()))
        service = client.webapp()
        operation = scenario["operation"]
        if operation == "download-task-file":
            stream = service.download_task_file("conversation/1", "task/1", "file/1", *opts)
        elif operation == "preview-task-file":
            stream = service.preview_task_file("conversation/1", "task/1", "file/1", *opts)
        else:
            stream = None
        if stream is not None:
            try:
                result = stream.read()
            finally:
                stream.close()
            self.assertEqual(result, base64.b64decode(scenario["response_base64"]))
        else:
            content = base64.b64decode(scenario["input"]["content_base64"])
            result = service.upload_file(
                scenario["input"]["filename"], content, *opts, content_type=scenario["input"]["content_type"],
            )
            self.assertEqual(result, scenario["response"]["data"])

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario["query"])
        for key in ("workspace", "role", "api_key", "authorization", "cookie", "runtime"):
            self.assertIsNone(observed[key], key)
        self.assertEqual(observed["probe"], "preserved")
        if operation != "upload-file":
            self.assertEqual(observed["accept"], "*/*")
            self.assertIsNone(observed["content_type"])
            self.assertEqual(observed["body"], b"")
            return
        self.assertEqual(observed["accept"], "application/json")
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + observed["content_type"].encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + observed["body"]
        )
        parts = list(message.iter_parts())
        self.assertEqual(len(parts), 1)
        part = parts[0]
        self.assertEqual(part.get_param("name", header="content-disposition"), "file")
        self.assertEqual(part.get_filename(), scenario["input"]["filename"])
        expected_part = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + scenario["input"]["content_type"].encode() + b"\r\n\r\n"
        )
        self.assertEqual(part.get_content_type(), expected_part.get_content_type())
        self.assertEqual(part.get_param("charset"), expected_part.get_param("charset"))
        self.assertEqual(part.get_payload(decode=True), base64.b64decode(scenario["input"]["content_base64"]))


if __name__ == "__main__":
    unittest.main()
