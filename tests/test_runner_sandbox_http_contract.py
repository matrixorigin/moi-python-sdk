import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class RunnerSandboxHTTPContractTest(unittest.TestCase):
    def test_public_requests_and_results_match_shared_go_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/runner_sandbox_http_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), json.loads(raw) if raw else None))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["response"]).encode())

            do_GET = record
            do_POST = record
            do_PATCH = record
            do_DELETE = record

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                service = client.runners("workspace-1") if case["domain"] == "runner" else client.sandboxes("workspace-1")
                args = [case["id"]] if "id" in case else []
                if "target_workspace_id" in case:
                    args.append(case["target_workspace_id"])
                if case["input"] is not None:
                    if case["domain"] == "runner":
                        args.append(case["input"]["name"])
                    else:
                        request_type = {
                            "create": sdk.SandboxCreateRequest,
                            "update-network": sdk.SandboxNetworkRequest,
                            "admin-update-network": sdk.SandboxNetworkRequest,
                            "update-quota": sdk.SandboxQuotaRequest,
                            "admin-update-quota": sdk.SandboxQuotaRequest,
                        }[case["operation"]]
                        args.append(json_format.ParseDict(case["input"], request_type()))
                args.extend(sdk.with_query_param(key, value) for key, value in case["query"].items())
                method = getattr(service, case["operation"].replace("-", "_"))
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        method(*args)
                    response = case["response"]
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (response["code"], response.get("msg", response.get("message")), case["status"]))
                else:
                    actual = method(*args)
                    operation = case["operation"]
                    if operation in ("delete", "admin-delete"):
                        self.assertIsNone(actual)
                    else:
                        if case["domain"] == "runner":
                            response_type = sdk.AgentRunner
                        else:
                            response_type = {
                                "get-quota": sdk.SandboxQuotaStatus,
                                "update-quota": sdk.SandboxQuota,
                                "admin-update-quota": sdk.SandboxQuota,
                                "admin-list": sdk.SandboxAdminListResult,
                                "terminal-token": sdk.SandboxTerminalToken,
                                "create-ssh-session": sdk.SandboxSSHSession,
                            }.get(operation, sdk.AgentSandbox)
                        data = case["response"]["data"]
                        expected = [json_format.ParseDict(item, response_type()) for item in data] if operation == "list" else json_format.ParseDict(data, response_type())
                        self.assertEqual(actual, expected)
                self.assertEqual(len(requests), 1)
                method_name, target, key, workspace, body = requests[0]
                endpoint = urllib.parse.urlsplit(target)
                self.assertEqual((method_name, endpoint.path, key, workspace), (case["method"], case["path"], "synthetic-key", "workspace-1"))
                self.assertEqual(urllib.parse.parse_qs(endpoint.query, keep_blank_values=True), {key: [value] for key, value in case["query"].items()})
                self.assertEqual(json.dumps(body, sort_keys=True), json.dumps(case["request"], sort_keys=True))

    def test_public_egress_endpoint_constructs_request(self):
        endpoint = sdk.SandboxEgressEndpoint(host="example.test", ports=[443])
        request = sdk.SandboxNetworkRequest(egress_endpoints=[endpoint])
        self.assertEqual(request.egress_endpoints[0], endpoint)
