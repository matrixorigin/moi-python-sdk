import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AIStudioHTTPContractTest(unittest.TestCase):
    def test_requests_and_responses_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "ai_studio_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        current = {}
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def receive(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                target = urlsplit(self.path)
                observed.clear()
                observed.update({
                    "method": self.command, "path": target.path,
                    "query": parse_qs(target.query, keep_blank_values=True),
                    "authorization": self.headers.get("Authorization"),
                    "api_key": self.headers.get("X-API-Key"),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "body": json.loads(raw) if raw else None,
                })
                payload = json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = receive
            do_PUT = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_token("admin-token"))
        service = client.ai_studio()
        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                operation = scenario["operation"]
                if operation == "chat-model-policy":
                    result = service.chat_model_policy()
                elif operation == "service-slots":
                    result = service.service_slots()
                elif operation == "service-slot-candidates":
                    result = service.service_slot_candidates()
                elif operation == "service-slot-logs":
                    result = service.service_slot_logs(
                        sdk.with_service_slot_log_slot_id(""), sdk.with_service_slot_log_page_size(0)
                    )
                elif operation == "put-service-slot":
                    result = service.put_service_slot(
                        scenario["slot_id"], sdk.PutAIStudioServiceSlotRequest(**scenario["input"])
                    )
                else:
                    self.fail(f"unknown operation {operation}")
                self.assertEqual(result, scenario["response"]["data"])
                self.assertEqual(observed["body"], scenario["request"])
                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["authorization"], "Bearer admin-token")
                self.assertIsNone(observed["api_key"])
                self.assertIsNone(observed["workspace"])


if __name__ == "__main__":
    unittest.main()
