import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkspaceChatCompletionTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_billing_slot_is_sent_as_query_metadata(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((urlsplit(self.path), body))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"choices":[{"message":{"content":"answer"}}]}')

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
            result = client.models("workspace").workspace_chat_completion(
                sdk.WorkspaceChatCompletionRequest(model="model"),
                sdk.with_query_param("service_slot", "agent_chat"),
            )
            self.assertEqual("answer", result["choices"][0]["message"]["content"])
            self.assertEqual(1, len(requests))
            path, body = requests[0]
            self.assertEqual("/newmoi/workspaces/workspace/llm/chat/completions", path.path)
            self.assertEqual({"service_slot": ["agent_chat"]}, parse_qs(path.query))
            self.assertEqual("model", body["model"])
            self.assertNotIn("service_slot", body)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_stream_preserves_request_and_consumes_sse_lines(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, self.headers.get("X-Workspace-ID"), body))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(b'data: {"choices":[{"delta":{"content":"answer"}}]}\n\ndata: [DONE]\n\n')
            def log_message(self, *_):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("key"))
            stream = client.models("workspace").workspace_chat_completion_stream(sdk.WorkspaceChatCompletionRequest(model="model"))
            try:
                self.assertEqual(stream.readline(), b'data: {"choices":[{"delta":{"content":"answer"}}]}\n')
                self.assertEqual(stream.read(), b'\ndata: [DONE]\n\n')
            finally:
                stream.close()
            self.assertEqual(requests, [("/newmoi/workspaces/workspace/llm/chat/completions", "workspace", {"model":"model", "stream":True})])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
