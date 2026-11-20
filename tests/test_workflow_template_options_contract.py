import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class WorkflowTemplateOptionsContractTest(unittest.TestCase):
    def test_requests_responses_and_owner_errors_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/workflow_template_options_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def handle_request(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), bool(raw), json.loads(raw) if raw else None))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["response"]).encode())

            do_POST = do_PUT = do_GET = handle_request

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.workflows("workspace-1")
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                body = case["request"] or {}
                opts = []
                for field, helper in {"template_key": "key", "description": "description", "runtime_fields": "input_form", "is_builtin": "builtin"}.items():
                    if field in body:
                        opts.append(getattr(sdk, "with_workflow_template_" + helper)(body[field]))

                def invoke():
                    command = case["command"]
                    if command == "get-workflow-template":
                        return service.get_workflow_template(case["id"])
                    if command == "create-workflow-template":
                        handle, result = client.workspace("workspace-1").create_workflow_template(body["name"], body["dsl_yaml"], *opts)
                        self.assertEqual(handle.id, case["id"])
                        return result
                    if command == "update-mowl-workflow-template":
                        return client.workspace("workspace-1").workflow_template(case["id"]).update_mowl(body["name"], body["workflow"], *opts)
                    method = getattr(service, command.replace("-", "_"))
                    args = [case["id"]] if case["method"] == "PUT" else []
                    return method(*args, body["name"], body.get("workflow", body.get("dsl_yaml")), *opts)

                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        invoke()
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    result = invoke()
                    self.assertEqual(result, json_format.ParseDict(case["response"]["data"], sdk.WorkflowTemplate()))
                self.assertEqual(len(requests), 1)
                method, path, key, workspace, has_body, recorded = requests[0]
                self.assertEqual((method, path, key, workspace, has_body), (case["method"], "/newmoi" + case["path"], "synthetic-key", "workspace-1", case["request"] is not None))
                self.assertEqual(json.dumps(recorded, sort_keys=True), json.dumps(case["request"], sort_keys=True))
