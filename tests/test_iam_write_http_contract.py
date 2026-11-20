import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk
from moi_product_sdk.client import _path_id
from moi_product_sdk.client import _path_id

from loopback_http import loopback_proxy_environment


class IAMWriteHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_path_id_matches_go_segment_escaping(self):
        self.assertEqual(_path_id("$&+:=@/?#"), "$&+:=@%2F%3F%23")

    def test_path_id_matches_go_segment_escaping(self):
        self.assertEqual(_path_id("$&+:=@/?#"), "$&+:=@%2F%3F%23")

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/iam_write_http_contract.json").read_text())
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
                    query=parsed.query,
                    api_key=self.headers.get("X-API-Key"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(scenario["response"]).encode())

            do_POST = _handle
            do_PUT = _handle
            do_PATCH = _handle
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

        if operation == "put-user-role-bindings":
            result = service.put_user_role_bindings(input_value["user_id"], request(sdk.IAMUserRoleBindingsRequest))
        elif operation == "create-role":
            result = service.create_role(request(sdk.IAMRoleCreateRequest))
        elif operation == "update-role":
            result = service.update_role(input_value["role_id"], request(sdk.IAMRoleUpdateRequest))
        elif operation == "validate-object-grants":
            result = service.validate_object_grants(input_value["resource_type"], input_value["resource_id"], input_value["role_id"], request(sdk.IAMObjectGrantsMutationRequest))
        elif operation == "apply-object-grants":
            result = service.apply_object_grants(input_value["resource_type"], input_value["resource_id"], input_value["role_id"], request(sdk.IAMObjectGrantsMutationRequest))
        elif operation == "validate-data-privileges":
            result = service.validate_data_privileges(input_value["role_id"], request(sdk.IAMDataPrivilegeMutationRequest))
        elif operation == "apply-data-privileges":
            result = service.apply_data_privileges(input_value["role_id"], request(sdk.IAMDataPrivilegeMutationRequest))
        elif operation == "repair-data-privileges":
            result = service.repair_data_privileges(input_value["role_id"], input_value["repair_operation"], request(sdk.IAMDataPrivilegeRepairRequest))
        elif operation == "add-role-inheritance":
            result = service.add_role_inheritance(input_value["role_id"], request(sdk.IAMRoleInheritanceMutationRequest))
        elif operation == "remove-role-inheritance":
            result = service.remove_role_inheritance(input_value["role_id"], request(sdk.IAMRoleInheritanceMutationRequest))
        elif operation == "validate-application-policy":
            result = service.validate_application_policy(input_value["role_id"], request(sdk.IAMApplicationPolicyRequest))
        elif operation == "apply-application-policy":
            result = service.apply_application_policy(input_value["role_id"], request(sdk.IAMApplicationPolicyRequest))
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], "")
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])
        self._assert_result(scenario, result)

    def _assert_result(self, scenario, result):
        message_types = {
            "put-user-role-bindings": sdk.IAMUserRoleBindingsMutationResult,
            "create-role": sdk.IAMRoleCreateResult,
            "update-role": sdk.IAMRoleCreateResult,
            "validate-object-grants": sdk.IAMObjectGrantsMutationResult,
            "apply-object-grants": sdk.IAMObjectGrantsMutationResult,
            "validate-data-privileges": sdk.IAMDataPrivilegeValidationResult,
            "apply-data-privileges": sdk.IAMDataPrivilegeOperationResult,
            "repair-data-privileges": sdk.IAMDataPrivilegeOperationResult,
            "add-role-inheritance": sdk.IAMRoleInheritanceMutationResult,
            "remove-role-inheritance": sdk.IAMRoleInheritanceMutationResult,
            "validate-application-policy": sdk.IAMApplicationPolicyValidationResult,
            "apply-application-policy": sdk.IAMApplicationPolicyApplyResult,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], message_types[scenario["operation"]]())
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
