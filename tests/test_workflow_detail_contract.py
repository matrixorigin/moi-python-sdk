import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf.json_format import MessageToDict

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkflowDetailContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_preserves_notification_configuration_and_design_graph(self):
        notification = {
            "type": "http",
            "url": "https://callback.example/hook",
            "notify_workflow_states": ["COMPLETED", "FAILED"],
        }
        graph = {"nodes": [{"id": "start"}]}
        paths = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "code": "OK",
                    "data": {"workflow": {
                        "id": "workflow-1",
                        "notification_config": notification,
                        "design_graph": graph,
                    }},
                }).encode())

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
            detail = client.workflows("workspace-1").get("workflow-1").workflow
            self.assertEqual(notification, MessageToDict(detail.notification_config))
            self.assertEqual(graph, MessageToDict(detail.design_graph))
            self.assertEqual(["/newmoi/workflow/v2/workflow-apps/workflow-1"], paths)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
