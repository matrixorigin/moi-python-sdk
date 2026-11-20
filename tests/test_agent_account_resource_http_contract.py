import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentAccountResourceHTTPContractTest(unittest.TestCase):
    def test_requests_and_responses_match_shared_handler_contract(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "agent_account_resource_http_contract.json"
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
                    "method": self.command,
                    "path": target.path,
                    "query": parse_qs(target.query, keep_blank_values=True),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "authorization": self.headers.get("Authorization"),
                    "cookie": self.headers.get("Cookie"),
                    "body": json.loads(raw) if raw else None,
                })
                payload = json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = receive
            do_POST = receive
            do_PUT = receive
            do_PATCH = receive
            do_DELETE = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)

        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                observed.clear()
                auth = sdk.with_token("admin-token") if scenario["auth"] == "token" else sdk.with_api_key("user-key")
                client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", auth)
                service = client.agents("workspace-1")
                options = tuple(
                    sdk.with_query_values(key, *values)
                    for key, values in sorted(scenario["query"].items())
                )
                operation = scenario["operation"]
                if operation == "admin-feedback-tickets":
                    result = service.admin_feedback_tickets(*options)
                elif operation == "admin-feedback-ticket":
                    result = service.admin_feedback_ticket(scenario["ticket_id"])
                elif operation == "update-admin-feedback-ticket":
                    request = json_format.ParseDict(scenario["input"], sdk.FeedbackTicketAdminUpdateRequest())
                    result = service.update_admin_feedback_ticket(scenario["ticket_id"], request)
                elif operation == "create-feedback-github-issue":
                    result = service.create_feedback_github_issue(
                        scenario["ticket_id"], scenario["kind"], scenario["title"], scenario["body_text"], scenario["retry"]
                    )
                elif operation == "build-feedback-github-issue-draft":
                    result = service.build_feedback_github_issue_draft(scenario["ticket_id"], scenario["kind"])
                elif operation == "approve-feedback-reward":
                    request = json_format.ParseDict(scenario["input"], sdk.FeedbackTicketAdminUpdateRequest())
                    result = service.approve_feedback_reward(scenario["ticket_id"], request)
                elif operation == "create-feedback-ticket":
                    request = json_format.ParseDict(scenario["input"], sdk.FeedbackTicketCreateRequest())
                    result = service.create_feedback_ticket(request)
                elif operation == "my-feedback-tickets":
                    result = service.my_feedback_tickets(*options)
                elif operation == "resource-any":
                    result = service.resource_any(
                        scenario["method"], scenario["resource"], scenario["tail_path"], scenario["input"], *options
                    )
                else:
                    self.fail(f"unknown operation {operation}")

                self.assertEqual(result, scenario["response"]["data"])
                self.assertEqual(observed["body"], scenario["request"])
                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertIsNone(observed["cookie"])
                if scenario["auth"] == "token":
                    self.assertEqual(observed["authorization"], "Bearer admin-token")
                    self.assertIsNone(observed["api_key"])
                else:
                    self.assertEqual(observed["api_key"], "user-key")
                    self.assertIsNone(observed["authorization"])


if __name__ == "__main__":
    unittest.main()
