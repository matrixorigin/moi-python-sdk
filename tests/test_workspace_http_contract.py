import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkspaceHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/workspace_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def test_non_product_account_helpers_are_not_public(self):
        account = sdk.Client("http://example.invalid/newmoi", sdk.with_api_key("user-key")).account()
        for name in ("add_feedback", "feedbacks", "add_experience", "add_experience_slot", "update_password", "me_update_password", "contact"):
            self.assertFalse(hasattr(account, name), name)
        self.assertFalse(hasattr(sdk, "ErrPasswordRequired"))

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    api_key=self.headers.get("X-API-Key"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(scenario["response"]).encode())

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
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.workspaces()
        input_value = scenario.get("input", {})
        operation = scenario["operation"]
        result = None
        try:
            if operation == "list":
                options = ()
                if "name" in scenario.get("query", {}):
                    options = (sdk.with_workspace_name_filter(scenario["query"]["name"]),)
                result = service.list(*options)
            elif operation == "create":
                result = service.create(input_value["name"])
            elif operation == "claim":
                result = service.claim(input_value["workspace_id"])
            elif operation == "delete":
                result = service.delete(input_value["workspace_id"])
            elif operation == "creations":
                result = service.creations()
            elif operation == "start-creation":
                result = service.start_creation(input_value["name"])
            elif operation == "update":
                result = service.update(input_value["workspace_id"], input_value["name"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
        else:
            self.assertLess(scenario["status"], 400)
            self._assert_result(scenario, result)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], {key: [value] for key, value in scenario.get("query", {}).items()})
        self.assertEqual(observed["api_key"], "user-key")
        self.assertIsNone(observed["workspace"])
        self.assertEqual(observed["body"], scenario["request"])

    def _assert_result(self, scenario, result):
        operation = scenario["operation"]
        if operation in ("delete", "update"):
            self.assertIsNone(result)
            return
        message_types = {
            "list": sdk.WorkspaceListResult,
            "create": sdk.WorkspaceCreateResult,
            "claim": sdk.WorkspaceClaimResult,
            "creations": sdk.WorkspaceCreationsResult,
            "start-creation": sdk.WorkspaceCreationJob,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], message_types[operation]())
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
