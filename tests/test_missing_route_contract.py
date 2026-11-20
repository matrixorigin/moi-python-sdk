import unittest
from unittest.mock import patch
import moi_product_sdk as sdk
from moi_product_sdk.client import _parse_error


class MissingRouteContractTest(unittest.TestCase):
    def setUp(self):
        self.client = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key"))

    def test_workflow_pascal_case_contract(self):
        service = self.client.workflows("workspace")
        with patch.object(service, "_request", return_value={"ID": "version", "WorkflowDefinitionID": "workflow", "Version": 3, "ResultMode": 1}):
            got = service.version("workflow", "version")
            self.assertEqual((got.id, got.version, got.result_mode), ("version", 3, 1))

    def test_native_provisioner_and_rpc_contracts(self):
        with patch.object(self.client, "_request_endpoint", return_value={"items": [{"workspace_id": "workspace", "remote_version": "v1"}]}) as request:
            got = self.client.system().service_account_workspaces()
            self.assertEqual(got.items[0].remote_version, "v1")
            request.assert_called_once_with("GET", "http://localhost/api/v1/service-accounts/workspaces")
        with patch.object(self.client, "_request_endpoint", return_value={"jsonrpc": "2.0", "id": "rpc", "result": {"tools": []}}):
            got = self.client.runtime_gateway().mcp(sdk.RuntimeRPCRequest(jsonrpc="2.0", method="tools/list"))
            self.assertEqual(got.id.string_value, "rpc")
            self.assertIn("tools", got.result.fields)

    def test_nested_error_fields(self):
        got = _parse_error(403, '{"error":{"code":"actor_not_linked","message":"账号尚未关联","request_id":"owner","retryable":false}}'.encode())
        self.assertEqual((got.code, got.message, got.request_id, got.details), ("actor_not_linked", "账号尚未关联", "owner", {"retryable": "false"}))
        got = _parse_error(401, b'{"error":{"code":-32001,"message":"Denied"}}')
        self.assertEqual((got.code, got.message), ("-32001", "Denied"))
