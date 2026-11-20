import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class RuntimeMCPCancellationTest(unittest.TestCase):
    def test_notifications_preserve_empty_acknowledgement_and_errors(self):
        self.enterContext(loopback_proxy_environment())
        response = {"status": 202, "body": b""}
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append((self.path, body))
                self.send_response(response["status"])
                self.send_header("X-Request-ID", "notification-case")
                self.end_headers()
                self.wfile.write(response["body"])

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_token("test-task-grant"))
            request = sdk.RuntimeRPCRequest(jsonrpc="2.0", method="notifications/cancelled")
            request.params.update({"requestId": "exchange", "reason": "test"})
            calls = (
                ("/api/v1/mcp/http", lambda: client.runtime_gateway().mcp(request)),
                ("/newmoi/workspaces/workspace/agents/agent/mcp/http", lambda: client.agents("workspace").workspace_mcp("agent", request)),
            )
            for status, body, code in (
                (202, b"", None),
                (200, b"", "ErrResponseInvalid"),
                (202, b"{}", "ErrResponseInvalid"),
                (401, b'{"error":{"code":-32001,"message":"Denied"}}', "-32001"),
            ):
                response.update(status=status, body=body)
                for path, call in calls:
                    with self.subTest(path=path, status=status, body=body):
                        if code is None:
                            self.assertIsNone(call())
                        else:
                            with self.assertRaises(sdk.Error) as failure:
                                call()
                            self.assertEqual(code, failure.exception.code)
                            self.assertEqual("notification-case", failure.exception.request_id)
                        actual_path, actual_body = received[-1]
                        self.assertEqual(path, actual_path)
                        self.assertNotIn("id", actual_body)
                        self.assertEqual("exchange", actual_body["params"]["requestId"])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
