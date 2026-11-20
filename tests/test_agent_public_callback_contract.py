import base64
import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentPublicCallbackContractTest(unittest.TestCase):
    def test_shared_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_public_callback_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}
        response = base64.b64decode(scenario["response_base64"])
        request_body = base64.b64decode(scenario.get("body_base64", ""))

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                parsed = urllib.parse.urlsplit(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=self.rfile.read(int(self.headers.get("Content-Length", "0"))),
                    content_type=self.headers.get("Content-Type"),
                    accept=self.headers.get("Accept"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    runtime=self.headers.get("X-MOI-Runtime-Authorization"),
                    signature=self.headers.get("X-Provider-Signature"),
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", scenario["response_content_type"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

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
            sdk.with_api_key("private-key"),
            sdk.with_custom_header("X-Provider-Signature", "provider-signature"),
        )
        query = {key: values[0] for key, values in scenario.get("query", {}).items()}
        operation = scenario["operation"]
        try:
            if operation == "verify-channel-callback":
                result = client.verify_channel_callback(scenario["provider"], scenario["workspace_id"], scenario["credential_ref"], query)
            elif operation == "post-channel-callback":
                result = client.post_channel_callback(scenario["provider"], scenario["workspace_id"], scenario["credential_ref"], request_body, query)
            elif operation == "post-we-com-callback":
                result = client.post_wecom_callback(scenario["workspace_id"], scenario["credential_ref"], request_body, query)
            elif operation == "verify-ingress-callback":
                result = client.verify_ingress_callback(scenario["provider"], scenario["workspace_id"], scenario["connection_id"], query)
            elif operation == "post-ingress-callback":
                result = client.post_ingress_callback(scenario["provider"], scenario["workspace_id"], scenario["connection_id"], request_body, query)
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            expected_error = json.loads(response)
            self.assertEqual(error.code, str(expected_error["code"]))
            self.assertEqual(error.message, expected_error["message"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            self.assertEqual(result, response)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], request_body)
        self.assertEqual(observed["content_type"], scenario.get("content_type"))
        self.assertEqual(observed["accept"], scenario["accept"])
        self.assertEqual(observed["signature"], "provider-signature")
        for name in ("workspace", "api_key", "authorization", "cookie", "runtime"):
            self.assertIsNone(observed[name])


if __name__ == "__main__":
    unittest.main()
