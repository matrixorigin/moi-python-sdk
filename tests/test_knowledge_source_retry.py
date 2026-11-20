import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class KnowledgeSourceRetryTest(unittest.TestCase):
    def test_reconcile_transmits_selected_source_and_preserves_result(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                requests.append((self.path, self.headers.get("X-Workspace-ID"), json.loads(raw) if raw else None))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"code":"OK","data":{"updated":true}}')

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with loopback_proxy_environment():
                client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("test-pat"))
                knowledge = client.knowledge("ws-1")
                self.assertTrue(knowledge.reconcile_source_jobs("101").updated)
                self.assertTrue(knowledge.reconcile_source_jobs("101", retry_source_row_id="kb-source-failed").updated)
            self.assertEqual(requests, [
                ("/newmoi/semantic-models/101/source-jobs/reconcile", "ws-1", None),
                ("/newmoi/semantic-models/101/source-jobs/reconcile", "ws-1", {"retry_source_row_id": "kb-source-failed"}),
            ])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
