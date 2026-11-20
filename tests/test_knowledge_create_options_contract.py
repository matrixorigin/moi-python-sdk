import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class KnowledgeCreateOptionsContractTest(unittest.TestCase):
    def test_catalog_and_source_selection_match_owner_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "knowledge_create_options_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        requests = []
        current = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), body))
                payload = json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

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
                body = case["request"]
                opts = []
                if "target_catalog_id" in body:
                    opts.append(sdk.with_semantic_model_with_sources_target_catalog_id(body["target_catalog_id"]))
                if "source_selections" in body:
                    selections = [sdk.SemanticModelSourceSelectionInput(**value) for value in body["source_selections"]]
                    opts.append(sdk.with_semantic_model_with_sources_source_selections(*selections))
                sources = [sdk.SemanticModelSourceInput(**value) for value in body["sources"]]
                if case["status"] >= 400:
                    with self.assertRaises(sdk.Error) as failure:
                        service.create_with_sources(body["name"], sources, *opts)
                    self.assertEqual((failure.exception.code, failure.exception.message, failure.exception.status), (case["response"]["code"], case["response"]["msg"], case["status"]))
                else:
                    result = service.create_with_sources(body["name"], sources, *opts)
                    self.assertEqual((result.model.id, result.data_domain.catalog_id), (101, 17))
                self.assertEqual(requests, [("POST", "/newmoi/semantic-models/create-with-sources", "workspace-1", body)])
