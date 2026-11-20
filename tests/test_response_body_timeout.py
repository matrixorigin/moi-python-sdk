import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ResponseBodyTimeoutTest(unittest.TestCase):
    def test_timeout_after_headers_keeps_timeout_and_request_identity(self):
        self.enterContext(loopback_proxy_environment())

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.send_header("X-Request-ID", "slow-query-body")
                self.end_headers()
                self.wfile.flush()
                time.sleep(0.15)
                try:
                    self.wfile.write(b'{"code":"OK","data":{"output":{}}}')
                except (BrokenPipeError, ConnectionResetError):
                    pass  # The client deliberately canceled the body read.

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("test-key"), sdk.with_timeout(0.03))
            with self.assertRaises(sdk.Error) as raised:
                client.knowledge("workspace").query(sdk.KnowledgeQueryRequest(sql="SELECT 1"))
            self.assertEqual("ErrTimeout", raised.exception.code)
            self.assertEqual("slow-query-body", raised.exception.request_id)
            self.assertEqual(200, raised.exception.status)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
