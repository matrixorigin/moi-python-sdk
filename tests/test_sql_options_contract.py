import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class SQLOptionsContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_requests_and_responses_match_shared_handler_contract(self):
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/sql_options_contract.json").read_text())
        current = {}
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append({
                    "method": self.command,
                    "path": self.path,
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "body": json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
                })
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["envelope"]).encode())

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        sql = client.sql("workspace-1")

        # Each adapter calls public SDK options; expected HTTP comes from the same
        # fixture as Go and CLI, including exact integers beyond float precision.
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                values = case["input"]
                command = case["command"]
                prefixes = {
                    "workbooks": "with_workbook_", "workbook-versions": "with_workbook_version_",
                    "query-history-overview": "with_query_history_overview_", "query-history": "with_query_history_",
                    "query-detail": "with_query_record_", "query-profile": "with_query_record_",
                    "execute-query": "with_sql_query_", "query-result": "with_sql_result_",
                    "execute": "with_sql_query_", "run": "with_sql_query_",
                }
                required = {"workbook-versions": "workbook_id", "query-detail": "statement_id", "query-profile": "statement_id", "execute-query": "query", "query-result": "statement_id", "execute": "query", "run": "query"}.get(command)
                suffixes = {"user": "users", "query_type": "types", "duration": "min_duration", "selected_field": "selected_fields", "sql_source_type": "sql_source_types", "sql_type": "type"}
                opts = []
                for field, value in values.items():
                    if field == required:
                        continue
                    factory = getattr(sdk, prefixes[command] + suffixes.get(field, field))
                    opts.append(factory(*value) if isinstance(value, list) else factory(value))
                args = [values[required]] if required else []
                method = {"execute": "execute_query", "run": "run_query"}.get(command, command.replace("-", "_"))
                failure = None
                try:
                    result = getattr(sql, method)(*args, *opts)
                except sdk.Error as caught:
                    failure = caught
                self.assertEqual(len(requests), 1)
                recorded = requests[0]
                self.assertEqual(recorded["method"], "POST")
                self.assertEqual(recorded["path"], "/newmoi" + case["path"])
                self.assertEqual(recorded["workspace"], "workspace-1")
                self.assertEqual(recorded["api_key"], "synthetic-key")
                self.assertEqual(json.dumps(recorded["body"], sort_keys=True), json.dumps(case["request"], sort_keys=True))
                if "error_code" in case:
                    self.assertIsInstance(failure, sdk.Error)
                    self.assertEqual(failure.code, case["error_code"])
                    self.assertEqual(failure.status, case["status"])
                    self.assertEqual(failure.message, case["envelope"].get("msg") or case["envelope"]["message"])
                else:
                    self.assertIsNone(failure)
                    expected = json_format.ParseDict(case["response"], type(result)())
                    self.assertEqual(result, expected)
