import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkspaceModelHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/workspace_model_http_contract.json").read_text())
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
                observed.update(
                    method=self.command,
                    path=self.path,
                    api_key=self.headers.get("X-API-Key"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if scenario["response"] is not None:
                    self.wfile.write(json.dumps(scenario["response"]).encode())

            do_GET = _handle
            do_POST = _handle
            do_PUT = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(
            f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key")
        )
        service = client.models("workspace-1")
        kind = scenario["kind"]
        operation = scenario["operation"]
        backend_id = scenario.get("id", 0)
        result = None

        def request(message_type):
            return json_format.ParseDict(scenario["input"], message_type())

        try:
            if operation == "create-backend":
                result = getattr(service, f"create_workspace_{kind}_backend")(
                    request(sdk.WorkspaceLLMBackendCreateRequest)
                )
            elif operation == "list-backends":
                result = getattr(service, f"list_workspace_{kind}_backends")()
            elif operation == "get-backend":
                result = getattr(service, f"get_workspace_{kind}_backend")(backend_id)
            elif operation == "update-backend":
                result = getattr(service, f"update_workspace_{kind}_backend")(
                    backend_id, request(sdk.WorkspaceLLMBackendUpdateRequest)
                )
            elif operation == "delete-backend":
                result = getattr(service, f"delete_workspace_{kind}_backend")(backend_id)
            elif operation == "create-endpoint":
                result = getattr(service, f"create_workspace_{kind}_endpoint")(
                    backend_id, scenario["address"]
                )
            elif operation == "list-endpoints":
                result = getattr(service, f"list_workspace_{kind}_endpoints")(backend_id)
            elif operation == "router":
                result = getattr(service, f"workspace_{kind}_router")()
            elif operation == "update-router":
                result = getattr(service, f"update_workspace_{kind}_router")(
                    request(sdk.WorkspaceLLMRouterUpdateRequest)
                )
            elif operation == "set-endpoint-status":
                result = getattr(service, f"set_workspace_{kind}_endpoint_status")(
                    backend_id, scenario["endpoint_id"], scenario["status_value"]
                )
            elif operation == "list-models":
                result = service.list_workspace_llm_models()
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
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])

    def _assert_result(self, scenario, result):
        operation = scenario["operation"]
        if operation in ("delete-backend", "set-endpoint-status") and (
            operation == "delete-backend" or scenario["kind"] == "llm"
        ):
            self.assertIsNone(result)
            return
        data = scenario["response"]["data"]
        if operation == "list-endpoints":
            expected = [json_format.ParseDict(item, sdk.WorkspaceLLMEndpoint()) for item in data]
            self.assertEqual(result, expected)
            self.assertEqual(result[0].id, scenario["endpoint_id"])
            return
        message_types = {
            "create-backend": sdk.WorkspaceLLMBackend,
            "list-backends": sdk.WorkspaceLLMBackendList,
            "get-backend": sdk.WorkspaceLLMBackend,
            "update-backend": sdk.WorkspaceLLMBackend,
            "create-endpoint": sdk.WorkspaceLLMEndpoint,
            "router": sdk.WorkspaceLLMRouterConfigResult,
            "update-router": sdk.WorkspaceLLMRouterConfigResult,
            "set-endpoint-status": sdk.WorkspaceEndpointMutationResult,
            "list-models": sdk.ProviderModelListResult,
        }
        expected = json_format.ParseDict(data, message_types[operation]())
        self.assertEqual(result, expected)
        if operation == "set-endpoint-status":
            self.assertTrue(result.updated)


if __name__ == "__main__":
    unittest.main()
