import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class SQLRemainingHTTPContractTest(unittest.TestCase):
    """One case per SQL/Workbook JSON route, driven through typed SDK entries."""

    def test_requests_and_responses_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads(
            (Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "sql_remaining_http_contract.json").read_text()
        )
        self.assertEqual(len(cases), 22)
        current = {}
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                requests.append({
                    "method": self.command,
                    "path": urlsplit(self.path).path,
                    "query": urlsplit(self.path).query,
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "content_type": self.headers.get("Content-Type"),
                    "body": json.loads(body) if body else None,
                })
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["envelope"]).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        sql = client.sql("workspace-1")
        catalog = client.catalog("workspace-1")

        for case in cases:
            with self.subTest(case=case["api"], route=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                try:
                    result = self._call(sql, catalog, case)
                except sdk.Error as failure:
                    result = failure
                self.assertEqual(len(requests), 1, case["name"])
                recorded = requests[0]
                self.assertEqual(recorded["method"], case["method"])
                self.assertEqual(recorded["path"], "/newmoi" + case["path"])
                self.assertEqual(recorded["query"], case["query"])
                self.assertEqual(recorded["workspace"], "workspace-1")
                self.assertEqual(recorded["api_key"], "synthetic-key")
                if case.get("bodyless"):
                    # Routes without a request DTO: the typed entries send no body,
                    # or an empty object when the SDK keeps an empty request body.
                    self.assertIn(recorded["body"], (None, {}))
                else:
                    self.assertEqual(recorded["content_type"], "application/json")
                    self.assertEqual(
                        json.dumps(recorded["body"], sort_keys=True),
                        json.dumps(case["request"], sort_keys=True),
                    )
                if "error_code" in case:
                    self.assertIsInstance(result, sdk.Error, case["name"])
                    self.assertEqual(result.code, case["error_code"])
                    self.assertEqual(result.status, case["status"])
                    self.assertEqual(result.message, case["envelope"].get("msg") or case["envelope"]["message"])
                    continue
                self.assertNotIsInstance(result, sdk.Error, case["name"])
                if case["response"] is None:
                    self.assertIsNone(result)
                    continue
                expected = json_format.ParseDict(case["response"], type(result)())
                self.assertEqual(result, expected)

    def _call(self, sql, catalog, case):
        values = case["input"]
        command = case["command"]
        if command == "drop-meta-database":
            return sql.drop_meta_database(values["db_name"])
        if command == "meta-databases":
            return sql.meta_databases()
        if command == "meta-db-tables":
            return sql.meta_db_tables(values["db_name"])
        if command == "meta-db-tree":
            return sql.meta_db_tree()
        if command == "meta-table-info":
            return sql.meta_table_info(values["db_name"], values["table_name"])
        if command == "meta-table-columns":
            return sql.meta_table_columns(values["db_name"], values["table_name"])
        if command == "meta-table-column-stats":
            return sql.meta_table_column_stats(values["db_name"], values["table_name"])
        if command == "meta-table-ddl":
            return sql.meta_table_ddl(values["db_name"], values["table_name"])
        if command == "drop-meta-table":
            return sql.drop_meta_table(values["db_name"], values["table_name"])
        if command == "drop-meta-view":
            return sql.drop_meta_view(values["db_name"], values["table_name"])
        if command == "describe-query":
            return sql.describe_query(values["query_id"])
        if command == "kill-query":
            return sql.kill_query(values["query_id"])
        if command == "workspace-table-columns":
            request = sdk.WorkspaceTableColumnsRequest(
                database_id=case["sdk_request"]["database_id"],
                table_id=case["sdk_request"]["table_id"],
                table_name=case["sdk_request"]["table_name"],
            )
            return catalog.workspace_table_columns(request)
        if command == "workspace-database-tables":
            return catalog.workspace_database_tables(values["database_id"])
        if command == "workspace-table-overview":
            return catalog.workspace_table_overview()
        if command == "create-workbook":
            return sql.create_workbook(values["name"])
        if command == "delete-workbook":
            return sql.delete_workbook(values["workbook_id"])
        if command == "workbook-detail":
            return sql.workbook_detail(values["workbook_id"], values["version_id"])
        if command == "update-workbook":
            return sql.update_workbook(values["workbook_id"], values["name"])
        if command == "create-workbook-version":
            return sql.create_workbook_version(values["workbook_id"], values["sql_content"])
        if command == "save-workbook-version":
            return sql.save_workbook_version(
                values["workbook_id"], values["version_id"], values["sql_content"]
            )
        if command == "update-workbook-version":
            return sql.update_workbook_version(
                values["workbook_id"], values["version_id"], values["sql_content"]
            )
        raise AssertionError(f"unknown fixture command {command}")


if __name__ == "__main__":
    unittest.main()
