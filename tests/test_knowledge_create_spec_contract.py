import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class KnowledgeCreateSpecContractTest(unittest.TestCase):
    def test_creation_controls_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/knowledge_create_spec_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(current["response"]).encode())

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        service = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key")).knowledge("workspace-1")
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                spec = sdk.SemanticModelCreateSpec(**case["spec"])
                opts = [getattr(sdk, "with_semantic_model_" + field)(value) for field, value in case["options"].items()]
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        service.create_with_spec(spec, *opts)
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    result = service.create_with_spec(spec, *opts)
                    expected = json_format.ParseDict(case["response"]["data"], sdk.SemanticModelInfo())
                    self.assertEqual(result, expected)
                self.assertEqual(len(requests), 1)
                method, path, key, workspace, body = requests[0]
                self.assertEqual((method, path, key, workspace), ("POST", "/newmoi/semantic-models", "synthetic-key", "workspace-1"))
                self.assertEqual(json.dumps(body, sort_keys=True), json.dumps(case["request"], sort_keys=True))
