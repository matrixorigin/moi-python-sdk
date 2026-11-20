import copy
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from moi_product_sdk.client import _a2a_follow_error
from loopback_http import loopback_proxy_environment


class ProductErrorDetailsContractTest(unittest.TestCase):
    def test_errors_match_shared_owner_details_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/product_error_details_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), json.loads(raw) if raw else None))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Request-ID", "transport-request")
                self.end_headers()
                self.wfile.write(json.dumps(current["response"]).encode())

            do_GET = record
            do_PATCH = record

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).dashboard("workspace-1")
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                with self.assertRaises(sdk.Error) as raised:
                    if case["operation"] == "download-chart-result":
                        result = service.download_chart_result("dashboard-1", "chart-1")
                        result.close()
                    else:
                        service.update("dashboard-1", json_format.ParseDict(case["input"], sdk.DataDashboardMutationRequest()))
                failure = raised.exception
                self.assertEqual((failure.code, failure.status, failure.request_id), (case["expected_code"], case["status"], "transport-request"))
                method, path = "PATCH", "/newmoi/data-dashboards/dashboard-1"
                if case["operation"] == "download-chart-result":
                    method, path = "GET", path + "/charts/chart-1/result/download"
                self.assertEqual(requests, [(method, path, "synthetic-key", "workspace-1", case["input"])])
                response = case["response"]
                message = response.get("msg") or response.get("message")
                if case["expected_code"] == "ErrResponseInvalid":
                    self.assertTrue(failure.message)
                    self.assertNotEqual(failure.message, message)
                    self.assertEqual(failure.details, {})
                    continue
                self.assertEqual(failure.message, message)
                # JSON comparison also distinguishes false from zero and keeps
                # the exact large integer received by the JSON decoder.
                self.assertEqual(json.dumps(failure.details, sort_keys=True), json.dumps(response.get("details") or {}, sort_keys=True))
                self.assertEqual(failure.data, response.get("data"))
                if "follow_task_id" in case:
                    before = copy.deepcopy(failure.details)
                    followed = _a2a_follow_error(case["follow_task_id"], failure)
                    self.assertEqual(followed.details, {**before, "task_id": case["follow_task_id"]})
                    self.assertEqual(failure.details, before)
                    self.assertEqual((followed.code, followed.message, followed.status, followed.request_id, followed.data), (failure.code, failure.message, failure.status, failure.request_id, failure.data))
