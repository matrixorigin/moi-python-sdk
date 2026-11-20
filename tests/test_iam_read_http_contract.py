import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class IAMReadHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/iam_read_http_contract.json").read_text())
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
            do_PUT = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.iam("workspace-1")
        input_value = scenario.get("input", {})
        operation = scenario["operation"]

        def request(message_type):
            return json_format.ParseDict(input_value["request"], message_type())

        if operation == "permission-schema":
            result = service.permission_schema()
        elif operation == "roles":
            result = service.roles()
        elif operation == "user-role-bindings":
            result = service.user_role_bindings(input_value["user_id"])
        elif operation == "role-permission-view":
            result = service.role_permission_view(input_value["role_id"])
        elif operation == "update-role-lifecycle":
            result = service.update_role_lifecycle(input_value["role_id"], request(sdk.IAMRoleLifecycleRequest))
        elif operation == "delete-role":
            result = service.delete_role(input_value["role_id"], request(sdk.IAMRoleDeleteRequest))
        elif operation == "transfer-object-ownership":
            result = service.transfer_object_ownership(input_value["resource_type"], input_value["resource_id"], request(sdk.IAMObjectOwnershipTransferRequest))
        elif operation == "object-permission-view":
            result = service.object_permission_view(input_value["resource_type"], input_value["resource_id"])
        elif operation == "data-privileges":
            result = service.data_privileges(input_value["role_id"])
        elif operation == "data-privilege-operation":
            result = service.data_privilege_operation(input_value["role_id"], input_value["request_id"])
        elif operation == "current-principal-roles":
            result = service.current_principal_roles()
        elif operation == "current-principal-capabilities":
            result = service.current_principal_capabilities(*input_value["capability_ids"])
        elif operation == "role-inheritance":
            result = service.role_inheritance(input_value["role_id"])
        elif operation == "role-inheritance-graph":
            result = service.role_inheritance_graph(input_value["role_id"])
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])
        self._assert_result(scenario, result)

    def _assert_result(self, scenario, result):
        message_types = {
            "permission-schema": sdk.IAMPermissionSchemaResult,
            "roles": sdk.IAMRoleListResult,
            "user-role-bindings": sdk.IAMUserRoleBindingsResult,
            "role-permission-view": sdk.IAMRolePermissionViewResult,
            "update-role-lifecycle": sdk.IAMRoleMutationResult,
            "delete-role": sdk.IAMRoleMutationResult,
            "transfer-object-ownership": sdk.IAMObjectOwnershipTransferResult,
            "object-permission-view": sdk.IAMObjectPermissionViewResult,
            "data-privileges": sdk.IAMDataPrivilegeViewResult,
            "data-privilege-operation": sdk.IAMDataPrivilegeOperationResult,
            "current-principal-roles": sdk.IAMCurrentPrincipalRolesResult,
            "current-principal-capabilities": sdk.IAMCurrentPrincipalCapabilitiesResult,
            "role-inheritance": sdk.IAMRoleInheritanceResult,
            "role-inheritance-graph": sdk.IAMRoleInheritanceResult,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], message_types[scenario["operation"]]())
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
