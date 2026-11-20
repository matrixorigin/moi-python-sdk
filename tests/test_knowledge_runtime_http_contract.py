import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class KnowledgeRuntimeHTTPContractTest(unittest.TestCase):
    def test_requests_and_results_match_shared_go_contract(self):
        self.enterContext(loopback_proxy_environment())
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/knowledge_runtime_http_contract.json").read_text())
        current, requests = {}, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                requests.append((self.command, self.path, self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), self.headers.get("X-MOI-Runtime-Authorization"), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
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
        # Authentication is API key only; live-task authorization is a required
        # operation header, represented by synthetic proof in this receiver.
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"), sdk.with_runtime_authorization("synthetic-live-task"))
        service = client.knowledge("workspace-1")
        types = {"find-files": sdk.KnowledgeFindFilesRequest, "search": sdk.KnowledgeSearchRequest, "read-document": sdk.KnowledgeReadDocumentRequest, "search-document": sdk.KnowledgeSearchDocumentRequest, "search-images": sdk.KnowledgeSearchImagesRequest, "read-evidence": sdk.KnowledgeReadEvidenceRequest, "describe-tables": sdk.KnowledgeDescribeTablesRequest, "query": sdk.KnowledgeQueryRequest, "cite": sdk.KnowledgeCiteRequest}
        for case in cases:
            with self.subTest(case=case["name"]):
                current.clear()
                current.update(case)
                requests.clear()
                request = json_format.ParseDict(case["input"], types[case["operation"]]())
                method = getattr(service, case["operation"].replace("-", "_"))
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as raised:
                        method(request)
                    self.assertEqual((raised.exception.code, raised.exception.message, raised.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    result = method(request)
                    self.assertEqual(result, json_format.ParseDict(case["response"]["data"], sdk.KnowledgeRuntimeResult()))
                self.assertEqual(len(requests), 1)
                method_name, path, key, workspace, proof, body = requests[0]
                self.assertEqual((method_name, path, key, workspace, proof), ("POST", "/newmoi/semantic-models/runtime/" + case["operation"], "synthetic-key", "workspace-1", "synthetic-live-task"))
                self.assertEqual(json.dumps(body, sort_keys=True), json.dumps(case["request"], sort_keys=True))
