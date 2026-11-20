import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ConversationRemainingHTTPContractTest(unittest.TestCase):
    def test_requests_responses_and_errors_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "conversation_remaining_http_contract.json"
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
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "body": json.loads(raw) if raw else None,
                })
                payload = b"" if current["status"] == 204 else json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                for key, value in current.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if payload:
                    self.wfile.write(payload)

            do_GET = receive
            do_POST = receive
            do_PUT = receive
            do_DELETE = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.conversations("workspace-1")
        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                options = tuple(sdk.with_query_values(key, *values) for key, values in sorted(scenario["query"].items()))
                operation = scenario["operation"]
                try:
                    if operation == "resource-any":
                        result = client.agents("workspace-1").resource_any(
                            scenario["method"], scenario["resource"], scenario["tail_path"], None, *options
                        )
                    elif operation == "get-message":
                        result = service.get_message(scenario["message_id"])
                    elif operation == "list-message-tags":
                        result = service.list_message_tags(scenario["message_id"])
                    elif operation == "remove-message-tag":
                        result = service.remove_message_tag(scenario["message_id"], scenario["source"], scenario["tag_name"])
                    elif operation == "list-sessions":
                        result = service.list_sessions(*options)
                    elif operation == "delete-session":
                        result = service.delete_session(scenario["session_id"])
                    elif operation == "get-session":
                        result = service.get_session(scenario["session_id"])
                    elif operation == "list-messages":
                        result = service.list_messages(scenario["session_id"], *options)
                    elif operation == "latest-message-id":
                        result = service.latest_message_id(scenario["session_id"])
                    elif operation == "append-modified-response":
                        result = service.append_modified_response(scenario["session_id"], scenario["message_id"], scenario["content"])
                    elif operation == "modify-response":
                        result = service.modify_response(scenario["session_id"], scenario["message_id"], scenario["content"])
                    elif operation == "list-session-tags":
                        result = service.list_session_tags(scenario["session_id"])
                    elif operation == "remove-session-tag":
                        result = service.remove_session_tag(scenario["session_id"], scenario["source"], scenario["tag_name"])
                    elif operation == "list-tags":
                        result = service.list_tags(*options)
                    elif operation == "delete-tag":
                        result = service.delete_tag(scenario["source"], scenario["tag_name"])
                    else:
                        self.fail(f"unknown operation {operation}")
                except sdk.Error as error:
                    self.assertGreaterEqual(scenario["status"], 400)
                    self.assertEqual(error.code, scenario["response"]["code"])
                    self.assertEqual(error.message, scenario["response"]["msg"])
                    self.assertEqual(error.status, scenario["status"])
                    self.assertEqual(error.request_id, scenario["response_headers"]["X-Request-ID"])
                    result = None
                else:
                    self.assertLess(scenario["status"], 400)
                    if operation == "resource-any":
                        self.assertEqual(result, scenario["response"]["data"])
                    elif result is not None:
                        expected = json_format.ParseDict(scenario["response"]["data"], type(result)())
                        self.assertEqual(result, expected)

                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertEqual(observed["api_key"], "synthetic-key")
                self.assertEqual(observed["body"], scenario["request"])


if __name__ == "__main__":
    unittest.main()
