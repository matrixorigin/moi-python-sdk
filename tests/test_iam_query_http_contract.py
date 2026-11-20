import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class IAMQueryHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/iam_query_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

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

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.iam("workspace-1")
        input_value = scenario.get("input", {})
        query = scenario.get("query", {})
        operation = scenario["operation"]
        result = None
        try:
            if operation == "role-delete-impact":
                result = service.role_delete_impact(
                    input_value["role_id"],
                    input_value["expected_lifecycle_version"],
                    include_ownership=input_value.get("include_ownership", False),
                    ownership_cursor=input_value.get("ownership_cursor", ""),
                    ownership_limit=input_value.get("ownership_limit", 50),
                    transfer_requested=input_value.get("transfer_requested", False),
                )
            elif operation == "role-delete-ownerships":
                result = service.role_delete_ownerships(
                    input_value["role_id"],
                    cursor=input_value.get("cursor"),
                    limit=input_value.get("limit"),
                    transfer_requested=input_value.get("transfer_requested"),
                )
            elif operation == "role-members":
                options = tuple(sdk.with_query_param(key, query[key]) for key in ("cursor", "limit") if key in query)
                result = service.role_members(input_value["role_id"], *options)
            elif operation == "list-permission-resources":
                options = tuple(sdk.with_query_param(key, query[key]) for key in ("parent_id", "cursor", "q", "limit") if key in query)
                result = service.list_permission_resources(input_value["resource_type"], input_value["action_id"], input_value["purpose"], *options)
            elif operation == "batch-describe-permission-resources":
                result = service.batch_describe_permission_resources(input_value["resource_type"], input_value["action_id"], input_value["purpose"], input_value["resource_ids"])
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
        self.assertEqual(observed["query"], {key: [value] for key, value in query.items()})
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])

    def _assert_result(self, scenario, result):
        operation = scenario["operation"]
        message_types = {
            "role-delete-impact": sdk.IAMRoleDeleteImpactResult,
            "role-delete-ownerships": sdk.IAMRoleDeleteOwnershipList,
            "role-members": sdk.IAMRoleMembersResult,
        }
        if operation in message_types:
            expected = json_format.ParseDict(scenario["response"]["data"], message_types[operation]())
            self.assertEqual(result, expected)
        else:
            self.assertEqual(result, scenario["response"]["data"])


if __name__ == "__main__":
    unittest.main()
