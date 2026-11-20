import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class WorkspaceMemberHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/workspace_member_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def test_backend_ignored_options_are_not_public(self):
        for name in ("with_audit_operator_user_id", "with_fuzzy_member_filter", "with_user_password"):
            self.assertFalse(hasattr(sdk, name), name)

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
                    workspace=self.headers.get("X-Workspace-ID"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(scenario["response"]).encode())

            do_GET = _handle
            do_POST = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.workspace_members("workspace-1")
        input_value = scenario.get("input", {})
        operation = scenario["operation"]
        result = None

        if operation == "accept-invitation":
            result = service.accept_invitation(input_value["invitation_id"])
        elif operation == "current-principal":
            result = service.current_principal()
        elif operation == "members":
            options = []
            if input_value.get("page_present"):
                options.append(sdk.with_member_page(input_value["page"]))
            if input_value.get("page_size_present"):
                options.append(sdk.with_member_page_size(input_value["page_size"]))
            for filter_value in input_value.get("filters", []):
                options.append(sdk.with_member_filter(filter_value["name"], *filter_value["values"]))
            result = service.members(*options)
        elif operation == "invite":
            options = []
            if input_value.get("email_present"):
                options.append(sdk.with_user_email(input_value["email"]))
            if input_value.get("description_present"):
                options.append(sdk.with_user_description(input_value["description"]))
            if input_value.get("role_ids") is not None:
                options.append(sdk.with_user_role_ids(*input_value["role_ids"]))
            if input_value.get("auto_accept"):
                options.append(sdk.with_user_auto_accept(True))
            for tag in input_value.get("tags", []):
                options.append(sdk.with_create_user_tag(tag["id"], tag["value"]))
            result = service.invite(input_value["name"], input_value["default_role_id"], *options)
        elif operation == "member":
            result = service.member(input_value["user_id"])
        elif operation == "update":
            options = tuple(sdk.with_user_tag(tag["id"], tag["value"]) for tag in input_value.get("tags", []))
            result = service.update(input_value["user_id"], input_value["name"], input_value["description"], *options)
        elif operation == "delete":
            result = service.delete(input_value["user_id"])
        elif operation == "update-status":
            result = service.update_status(input_value["user_id"], input_value["action"])
        elif operation == "create-user-tag":
            result = service.create_user_tag(input_value["name"])
        elif operation == "user-tags":
            result = service.user_tags()
        elif operation == "update-user-tag":
            result = service.update_user_tag(input_value["tag_id"], input_value["name"])
        elif operation == "delete-user-tag":
            result = service.delete_user_tag(input_value["tag_id"])
        elif operation == "audit-logs":
            factories = {
                "method": sdk.with_audit_method,
                "result": sdk.with_audit_result,
                "status_code": lambda value: sdk.with_audit_status_code(int(value)),
                "start_time": sdk.with_audit_start_time,
                "end_time": sdk.with_audit_end_time,
                "page": lambda value: sdk.with_page(int(value)),
                "page_size": lambda value: sdk.with_page_size(int(value)),
            }
            options = tuple(factories[key](value) for key, value in sorted(scenario.get("query", {}).items()))
            result = service.audit_logs(*options)
        elif operation == "audit-log-overview":
            result = service.audit_log_overview()
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], {key: [value] for key, value in scenario.get("query", {}).items()})
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])
        self._assert_result(scenario, result)

    def _assert_result(self, scenario, result):
        operation = scenario["operation"]
        if operation in ("update", "delete", "update-status"):
            self.assertIsNone(result)
            return
        message_types = {
            "accept-invitation": sdk.WorkspaceInvitationAcceptResult,
            "current-principal": sdk.CurrentWorkspacePrincipalResult,
            "members": sdk.WorkspaceMemberListResult,
            "invite": sdk.WorkspaceMemberInviteResult,
            "member": sdk.WorkspaceMember,
            "create-user-tag": sdk.IDResult,
            "user-tags": sdk.DataTagListResult,
            "update-user-tag": sdk.IDResult,
            "delete-user-tag": sdk.IDResult,
            "audit-logs": sdk.AuditLogListResult,
            "audit-log-overview": sdk.AuditLogOverviewResult,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], message_types[operation]())
        self.assertEqual(result, expected)
        if operation == "create-user-tag":
            self.assertEqual(result.id, 9007199254740993)
        elif operation == "audit-log-overview":
            self.assertEqual(result.total, 9007199254740993)


if __name__ == "__main__":
    unittest.main()
