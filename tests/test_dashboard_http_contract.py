import json
import threading
import unittest
import urllib.parse
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from moi_product_sdk.client import SQLQueryResult
from loopback_http import loopback_proxy_environment


class DashboardHTTPContractTest(unittest.TestCase):
    def test_requests_and_results_match_shared_owner_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/dashboard_http_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), raw or b"null"))
                csv = current.get("csv")
                self.send_response(current["status"])
                self.send_header("Content-Type", "text/csv; charset=utf-8" if csv is not None else "application/json")
                self.end_headers()
                self.wfile.write(csv.encode() if csv is not None else json.dumps(current["response"]).encode())

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
        service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).dashboard("workspace-1")
        types = {
            "create": (sdk.DataDashboardMutationRequest, sdk.DataDashboard),
            "list": (sdk.DataDashboardListRequest, sdk.DataDashboardListResult),
            "get": (None, sdk.DataDashboard),
            "update": (sdk.DataDashboardMutationRequest, sdk.DataDashboardMutationResult),
            "delete": (None, sdk.DataDashboardMutationResult),
            "create-chart": (sdk.DataDashboardChartMutationRequest, sdk.DataDashboardChart),
            "update-chart": (sdk.DataDashboardChartMutationRequest, sdk.DataDashboardChart),
            "delete-chart": (None, sdk.DataDashboardMutationResult),
            "update-chart-order": (sdk.DataDashboardChartOrderRequest, sdk.DataDashboardChartOrderRequest),
            "preview-sql": (None, SQLQueryResult),
            "generate-sql": (None, sdk.DataDashboardGeneratedSQLResult),
            "refresh": (None, sdk.DataDashboardChartRuns),
            "run-chart": (None, sdk.DataDashboardChartRun),
            "chart-result": (None, sdk.DataDashboardChartExecution),
            "download-chart-result": (None, None),
            "drill-through": (sdk.DataDashboardDrillThroughRequest, sdk.DataDashboardDrillThroughResult),
            "download-drill-through": (sdk.DataDashboardDrillThroughRequest, None),
            "task-execution-overview": (None, None),
        }
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                request_type, response_type = types[case["operation"]]
                args = []
                for key in ("dashboard_id", "chart_id"):
                    if key in case:
                        args.append(case[key])
                if request_type is not None:
                    args.append(json_format.ParseDict(case["input"], request_type()))
                elif case["operation"] == "preview-sql":
                    args.append(case["input"]["sql_text"])
                    if "chart_id" in case["input"]:
                        args.append(sdk.with_dashboard_preview_chart_id(case["input"]["chart_id"]))
                elif case["operation"] == "generate-sql":
                    args.extend([case["input"]["question"], case["input"]["title"]])
                for name, value in case["query"].items():
                    args.append(sdk.with_query_param(name, value))
                method = getattr(service, case["operation"].replace("-", "_"))
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        method(*args)
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    result = method(*args)
                    if "csv" in case:
                        try:
                            self.assertEqual(result.read(), case["csv"].encode())
                        finally:
                            result.close()
                    elif case["operation"] == "task-execution-overview":
                        expected = case["response"]["data"]
                        self.assertEqual({key: getattr(result, key) for key in expected}, expected)
                    else:
                        self.assertEqual(result, json_format.ParseDict(case["response"]["data"], response_type()))
                self.assertEqual(len(requests), 1)
                method_name, raw_path, key, workspace, body = requests[0]
                path = urllib.parse.urlsplit(raw_path)
                self.assertEqual((method_name, path.path, key, workspace), (case["method"], case["path"], "synthetic-key", "workspace-1"))
                self.assertEqual(urllib.parse.parse_qs(path.query, keep_blank_values=True), {name: [value] for name, value in case["query"].items()})
                # Compare exact JSON numeric values: 0 and 0.0 are the same
                # number; false is a distinct type, and large IDs never round.
                def number(value):
                    return ("number", Decimal(value))

                self.assertEqual(
                    json.loads(body, parse_int=number, parse_float=number),
                    json.loads(json.dumps(case["request"]), parse_int=number, parse_float=number),
                )
