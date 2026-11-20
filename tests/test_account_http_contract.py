import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class AccountHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/account_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    accept=self.headers.get("Accept"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if not scenario.get("stream"):
                    self.wfile.write(json.dumps(scenario["response"]).encode())

            do_GET = _handle
            do_POST = _handle
            do_PATCH = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.account()
        input_value = scenario.get("input", {})
        operation = scenario["operation"]

        if operation == "current-credit":
            result = service.current_credit()
        elif operation == "db-connection":
            result = service.db_connection(input_value["workspace_id"])
        elif operation == "begin-browser-login":
            result = service.begin_browser_login(input_value["return_to"])
        elif operation == "complete-browser-login":
            request = json_format.ParseDict(input_value["browser_login"], sdk.BrowserLoginCallbackRequest())
            result = service.complete_browser_login(request)
        elif operation == "complete-browser-logout":
            result = service.complete_browser_logout(input_value["state"])
        elif operation == "browser-session":
            result = service.browser_session()
        elif operation == "logout-browser-session":
            request = json_format.ParseDict(input_value["browser_logout"], sdk.BrowserLogoutRequest())
            result = service.logout_browser_session(request)
        elif operation == "preferences":
            result = service.preferences()
        elif operation == "update-preferences":
            request = json_format.ParseDict(input_value["preferences"], sdk.AuthPreferencesRequest())
            result = service.update_preferences(request)
        elif operation == "checkin-status":
            result = service.checkin_status()
        elif operation == "registration-invite":
            result = service.registration_invite()
        elif operation == "reward-center-items":
            result = service.reward_center_items()
        elif operation == "reward-center-events":
            result = service.reward_center_events(input_value["event_type"])
        elif operation == "reward-center-invitations":
            result = service.reward_center_invitations(input_value["page"], input_value["page_size"])
        elif operation == "checkin":
            result = service.checkin(input_value["source"])
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], {key: [value] for key, value in scenario.get("query", {}).items()})
        self.assertEqual(observed["api_key"], "user-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertEqual(observed["workspace"], scenario.get("workspace_scope"))
        if scenario.get("stream"):
            self.assertEqual(observed["accept"], "*/*")
        self.assertEqual(observed["body"], scenario["request"])
        self._assert_result(scenario, result)

    def _assert_result(self, scenario, result):
        if scenario.get("stream"):
            self.assertIsInstance(result, sdk.StreamResponse)
            self.assertEqual(result.status, scenario["status"])
            self.assertEqual(result.headers.get("Location"), scenario["response_headers"]["Location"])
            result.close()
            return
        operation = scenario["operation"]
        message_types = {
            "current-credit": sdk.CurrentCreditResult,
            "db-connection": sdk.DBConnectionResult,
            "browser-session": sdk.BrowserSessionResult,
            "logout-browser-session": sdk.BrowserLogoutResult,
            "preferences": sdk.AuthPreferencesResult,
            "update-preferences": sdk.AuthPreferencesResult,
        }
        if operation in message_types:
            expected = json_format.ParseDict(scenario["response"]["data"], message_types[operation]())
            self.assertEqual(result, expected)
        else:
            self.assertEqual(result, scenario["response"]["data"])


if __name__ == "__main__":
    unittest.main()
