import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class WorkspaceFileListTest(unittest.TestCase):
    def test_workspace_discovery_keeps_filters_placement_and_runtime_identity(self):
        self.enterContext(loopback_proxy_environment())
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                requests.append((urlsplit(self.path), self.headers))
                body = json.dumps({"code": "OK", "data": {
                    "items": [{"id": 7, "volume_id": 3, "file_id": "f1", "file_name": "report.csv", "created_at": 100, "size": 12}],
                    "total": 2, "next_page_token": "next",
                }}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"), sdk.with_runtime_authorization("Bearer task-proof"))
            result = client.catalog("workspace").list_workspace_files(sdk.with_page_size(1), sdk.with_query_values("filter_file_id", "f1", "f2"))
            self.assertEqual((7, 3, "f1", 100, 12), (result.items[0].id, result.items[0].volume_id, result.items[0].file_id, result.items[0].created_at, result.items[0].size))
            self.assertEqual((2, "next"), (result.total, result.next_page_token))
            path, headers = requests[0]
            self.assertEqual("/newmoi/workspaces/workspace/files", path.path)
            self.assertEqual({"page_size": ["1"], "filter_file_id": ["f1", "f2"]}, parse_qs(path.query))
            self.assertEqual("Bearer task-proof", headers["X-MOI-Runtime-Authorization"])
            self.assertNotIn("X-MOI-Role-ID", headers)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
