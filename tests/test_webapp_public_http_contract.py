import base64
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class WebappPublicHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads(Path("../go-sdk/testdata/webapp_public_http_contract.json").read_text())
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
                    body=json.loads(raw) if raw else None,
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
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                self.send_header("Content-Type", scenario.get("response_content_type", "application/json"))
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle
            do_PATCH = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(
            f"http://127.0.0.1:{server.server_port}/newmoi",
            sdk.with_api_key("private-key"),
            sdk.with_token("private-token"),
            sdk.with_session_cookie("private-cookie"),
            sdk.with_runtime_authorization("private-runtime-grant"),
            sdk.with_workspace_current_role_id("workspace-1", "7"),
            sdk.with_custom_header("X-Webapp-Probe", "preserved"),
        )
        service = client.webapp()
        body = scenario["input"].get("body")
        opts = tuple(
            sdk.with_query_values(key, *values)
            for key, values in sorted(scenario.get("query", {}).items())
        )
        operation = scenario["operation"]
        try:
            if operation == "resolve":
                result = service.resolve(body)
            elif operation == "create-session":
                result = service.create_session(body)
            elif operation == "refresh-session":
                result = service.refresh_session(body)
            elif operation == "create-conversation":
                result = service.create_conversation(body, *opts)
            elif operation == "list-conversations":
                result = service.list_conversations(*opts)
            elif operation == "rename-conversation":
                result = service.rename_conversation("conversation/1", body, *opts)
            elif operation == "delete-conversation":
                result = service.delete_conversation("conversation/1", *opts)
            elif operation == "list-messages":
                result = service.list_messages("conversation/1", *opts)
            elif operation == "list-task-events":
                result = service.list_task_events("conversation/1", "task/1", *opts)
            elif operation == "submit-feedback":
                result = service.submit_feedback(body, *opts)
            elif operation == "call-mcp-app":
                result = service.call_mcp_app(body, *opts)
            elif operation == "read-mcp-app-resource":
                result = service.read_mcp_app_resource(body, *opts)
            elif operation == "a2a-stream":
                stream = service.a2a_stream(body, *opts)
                try:
                    result = stream.read()
                finally:
                    stream.close()
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertTrue(self._expects_error(scenario), error)
            if scenario["name"] == "malformed-envelope":
                self.assertEqual(error.code, "ErrResponseInvalid")
            else:
                self.assertEqual(error.code, str(scenario["response"]["code"]))
                self.assertEqual(error.message, scenario["response"]["message"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertFalse(self._expects_error(scenario))
            if operation == "a2a-stream":
                self.assertEqual(result, base64.b64decode(scenario["response_base64"]))
            else:
                self.assertEqual(result, scenario["response"]["data"])

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        for key in ("workspace", "role", "api_key", "authorization", "cookie", "runtime"):
            self.assertIsNone(observed[key], key)
        self.assertEqual(observed["probe"], "preserved")
        self.assertEqual(observed["accept"], "text/event-stream" if operation == "a2a-stream" else "application/json")
        self.assertEqual(observed["content_type"], "application/json" if "body" in scenario["input"] else None)

    @staticmethod
    def _expects_error(scenario):
        return scenario["status"] >= 400 or scenario["name"] == "malformed-envelope"


if __name__ == "__main__":
    unittest.main()
