import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class CatalogNavigationContractTest(unittest.TestCase):
    def test_requests_match_shared_go_and_cli_contract(self):
        self.enterContext(loopback_proxy_environment())
        fixture = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "catalog_navigation_contract.json"
        cases = json.loads(fixture.read_text(encoding="utf-8"))
        requests = []
        current = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), self.headers.get("X-API-Key"), body))
                payload = json.dumps({"code": "OK", "data": current["response"]}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        catalog = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).catalog("workspace-1")
        operations = {
            "tree": catalog.tree,
            "system-tree": catalog.system_tree,
            "database-table-leaves": catalog.database_table_leaves,
            "search-data-dashboard-tables": catalog.search_data_dashboard_tables,
        }
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                result = operations[case["command"]](**case["input"])
                self.assertEqual(requests, [("POST", "/newmoi" + case["path"], "workspace-1", "synthetic-key", case["request"])])
                self.assertEqual(result.next_page_token, case["response"].get("next_page_token", ""))
                if "total" in case["response"]:
                    self.assertEqual(result.total, case["response"]["total"])
