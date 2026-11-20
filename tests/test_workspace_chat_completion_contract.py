import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkspaceChatCompletionContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_request_and_stream_contract(self):
        fixture = json.loads(Path("../go-sdk/testdata/workspace_chat_completion_contract.json").read_text())
        bodies = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                bodies.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                if self.path != "/newmoi/workspaces/workspace-1/llm/chat/completions?service_slot=slot%2F1" or self.headers.get("X-Workspace-ID") != "workspace-1":
                    raise AssertionError((self.path, self.headers))
                self.send_response(200)
                self.send_header("Content-Type", "application/json" if len(bodies) == 1 else "text/event-stream")
                self.end_headers()
                payload = json.dumps(fixture["response"]).encode() if len(bodies) == 1 else fixture["stream"].encode()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        request = json_format.ParseDict(fixture["input"], sdk.WorkspaceChatCompletionRequest())
        options = (sdk.with_query_param("service_slot", "slot/1"),)
        result = client.models("workspace-1").workspace_chat_completion(request, *options)
        self.assertEqual(result["id"], "chat-1")
        stream = client.models("workspace-1").workspace_chat_completion_stream(request, *options)
        self.assertEqual(stream.read(), fixture["stream"].encode())
        stream.close()
        stream_expected = dict(fixture["expected"], stream=True)
        self.assertEqual(bodies, [fixture["expected"], stream_expected])


if __name__ == "__main__":
    unittest.main()
