import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class CatalogNavigationPaginationTest(unittest.TestCase):
    def test_navigation_sends_page_options_and_decodes_continuation(self):
        self.enterContext(loopback_proxy_environment())
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, body))
                key = "tree" if self.path.endswith("/tree") else "list"
                data = json.dumps({"code": "OK", "data": {key: [], "next_page_token": "next"}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
            catalog = client.catalog("workspace")
            options = [sdk.with_catalog_page_size(20), sdk.with_catalog_page_token("cursor")]
            self.assertEqual("next", catalog.list(*options).next_page_token)
            self.assertEqual("next", catalog.list_databases(10, *options).next_page_token)
            self.assertEqual("next", catalog.database_children(20, *options).next_page_token)
            self.assertEqual("next", catalog.tree(page_size=20, page_token="cursor", search="report", resource_types=["volume"], resource_id=7).next_page_token)
            self.assertEqual("next", catalog.system_tree(page_size=20, page_token="cursor", search="report", database_name="moi", table_name="report").next_page_token)
            database = sdk.DatabaseHandle(sdk.CatalogHandle(client.workspace("workspace"), 10, "catalog"), 20, "database")
            self.assertEqual("next", database.children(*options).next_page_token)
            for path, body in requests:
                self.assertEqual((20, "cursor"), (body["page_size"], body["page_token"]), path)
            self.assertEqual(("report", ["volume"], 7), (requests[3][1]["search"], requests[3][1]["resource_types"], requests[3][1]["resource_id"]))
            self.assertEqual("moi", requests[4][1]["database_name"])
            self.assertEqual("report", requests[4][1]["table_name"])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
