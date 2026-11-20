import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.parse import urlsplit

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class _ProductHandler(BaseHTTPRequestHandler):
    requests = []
    responses = {}

    def handle_request(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        self.requests.append((self.command, self.path, body, {key.lower(): value for key, value in self.headers.items()}))
        result = self.responses[(self.command, urlsplit(self.path).path)]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"code": "OK", "data": result}).encode())

    do_GET = do_POST = do_PUT = handle_request

    def log_message(self, *_args):
        pass


class SDK19808HTTPTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())
        _ProductHandler.requests = []
        _ProductHandler.responses = {}
        self.server = HTTPServer(("127.0.0.1", 0), _ProductHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("test-key"), sdk.with_workspace_current_role_id("ws/1", "7"))

    def test_iam_preserves_versions_diff_and_cursors(self):
        root = "/newmoi/workspaces/ws%2F1/iam"
        _ProductHandler.responses.update({
            ("GET", root + "/roles/role%2F7/ownership-impact"): {"owned_count": 1, "ownership_version": "set-v3", "items": [{"resource_id": "table-1", "ownership_version": 9007199254740993}]},
            ("GET", root + "/roles/role%2F7/audit-events"): {"events": [{"audit_event_id": "audit-1", "actor_display_name": "Alice", "diff": {"name": {"before": "old", "after": "new"}}, "policy_version": 3}], "next_cursor": "role-next", "trace_id": "trace-1"},
            ("GET", root + "/users/user%2F1/audit-events"): {"events": [{"summary": [{"key": "role", "value": "7"}], "lifecycle_version": "member-v2"}], "next_cursor": "user-next"},
            ("PUT", root + "/me/default-role"): {"default_role_id": "8", "default_role_version": 1, "audit_event_id": "default-audit", "idempotent_replay": True},
        })
        iam = self.client.iam("ws/1")
        impact = iam.ownership_impact("role/7", sdk.with_query_param("resource_type", "table"))
        self.assertEqual(impact.items[0].ownership_version, 9007199254740993)
        self.assertEqual(impact.ownership_version, "set-v3")
        role_audit = iam.role_audit_events("role/7", sdk.with_query_param("cursor", "next/1"))
        self.assertEqual(role_audit.events[0].diff["name"]["after"], "new")
        self.assertEqual((role_audit.next_cursor, role_audit.trace_id), ("role-next", "trace-1"))
        user_audit = iam.user_audit_events("user/1")
        self.assertEqual((user_audit.events[0].summary[0].value, user_audit.next_cursor), ("7", "user-next"))
        changed = iam.set_default_role(sdk.IAMSetDefaultRoleRequest(target_role_id="8", expected_default_role_version=0, request_id="set-1"))
        self.assertEqual((changed.default_role_id, changed.default_role_version, changed.idempotent_replay), ("8", 1, True))
        self.assertEqual(_ProductHandler.requests[-1][2], {"target_role_id": "8", "expected_default_role_version": 0, "request_id": "set-1"})
        for _method, _path, _body, headers in _ProductHandler.requests:
            self.assertEqual(headers["x-workspace-id"], "ws/1")
            self.assertEqual(headers["x-moi-role-id"], "7")

    def test_artifacts_keep_partial_results_and_numeric_versions(self):
        root = "/newmoi/workspaces/ws%2F1/agent-artifacts"
        failure = {"artifact_id": "missing", "version": 1, "reason": "permission_denied"}
        _ProductHandler.responses.update({
            ("GET", root): {"items": [{"artifact_id": "artifact/1", "version": 2}], "total": 3, "page": 2, "page_size": 1, "creator_sources": [{"created_by": "user-1", "creator_name": "Alice"}]},
            ("GET", root + "/artifact%2F1/versions/2"): {"artifact_id": "artifact/1", "version": 2, "size": 9007199254740993},
            ("POST", root + "/batch-delete"): {"succeeded": [{"artifact_id": "artifact/1", "version": 2}], "failed": [failure]},
            ("POST", root + "/resolve"): {"items": [{"artifact_id": "artifact/1", "version": 2, "file_id": "file-1"}], "failed": [failure]},
            ("POST", root + "/backfill"): {"scanned": 4, "inserted": 2, "skipped": 1, "failed": 1, "dry_run": True},
        })
        agents = self.client.agents("ws/1")
        listing = agents.artifacts(sdk.with_query_param("page", "2"))
        self.assertEqual((listing.page, listing.items[0].artifact_id, listing.creator_sources[0].creator_name), (2, "artifact/1", "Alice"))
        self.assertEqual(agents.artifact("artifact/1", 2).size, 9007199254740993)
        request = sdk.AgentArtifactBatchRequest(items=[sdk.AgentArtifactRef(artifact_id="artifact/1", version=2), sdk.AgentArtifactRef(artifact_id="missing", version=1)])
        deleted = agents.delete_artifacts(request)
        self.assertEqual((deleted.succeeded[0].version, deleted.failed[0].reason), (2, "permission_denied"))
        resolved = agents.resolve_artifacts(request)
        self.assertEqual((resolved.items[0].file_id, resolved.failed[0].artifact_id), ("file-1", "missing"))
        self.assertIs(type(_ProductHandler.requests[-1][2]["items"][0]["version"]), int)
        result = agents.backfill_artifacts(sdk.AgentArtifactBackfillRequest(dry_run=True, limit=4))
        self.assertEqual((result.inserted, result.failed, result.dry_run), (2, 1, True))
        self.assertEqual(_ProductHandler.requests[-1][2], {"dry_run": True, "limit": 4})


class _Socket:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.sent = []
        self.timeout = 9
        self.closed = False

    def send(self, payload):
        self.sent.append(json.loads(payload))

    def recv(self):
        return next(self.frames)

    def close(self):
        self.closed = True

    def gettimeout(self):
        return self.timeout

    def settimeout(self, timeout):
        self.timeout = timeout


class DashboardWebSocketTest(unittest.TestCase):
    def test_dashboard_protocol_and_identity(self):
        refusal = {"id": "update-1", "message_type": "error", "data": {"status": 403, "code": "ErrAccessDenied", "msg": "localized fixture message"}}
        socket = _Socket([
            json.dumps({"id": "ping-1", "message_type": "pong"}),
            json.dumps({"id": "preview-1", "message_type": "dashboard_preview_result", "data": {"status": "success", "total": 1}}),
            json.dumps({"id": "create-1", "message_type": "dashboard_chart_create_result", "data": {"ID": "chart-1"}}),
            json.dumps(refusal),
        ])
        client = sdk.Client("https://example.test/prefix/newmoi", sdk.with_api_key("test-key"), sdk.with_workspace_current_role_id("ws/1", "7"), sdk.with_custom_header("x-moi-role-id", "99"))
        with patch("websocket.create_connection", return_value=socket) as connect:
            session = client.dashboard("ws/1").connect_web_socket()
        args, kwargs = connect.call_args
        self.assertEqual(args[0], "wss://example.test/prefix/newmoi/data-dashboards/ws?workspace_id=ws%2F1")
        self.assertIn("X-MOI-Role-ID: 7", kwargs["header"])
        self.assertNotIn("x-moi-role-id: 99", kwargs["header"])
        self.assertEqual(kwargs["subprotocols"], ["moi-api-key", "moi-api-key.test-key", "moi-role-id.7"])
        session.ping("ping-1")
        self.assertEqual(session.receive(timeout=0.5).id, "ping-1")
        self.assertEqual(socket.timeout, 9)
        session.preview_sql("preview-1", "dashboard-1", "chart-1", "SELECT 1")
        self.assertEqual(session.receive().data["status"], "success")
        chart = sdk.DataDashboardChartMutationRequest(name="report", chart_type="table", sql_text="SELECT 1")
        session.create_chart("create-1", "dashboard-1", chart)
        self.assertEqual(session.receive().data["ID"], "chart-1")
        session.update_chart("update-1", "dashboard-1", "chart-1", chart)
        with self.assertRaises(sdk.Error) as raised:
            session.receive()
        self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message), (403, refusal["data"]["code"], refusal["data"]["msg"]))
        self.assertEqual(raised.exception.data["id"], "update-1")
        self.assertEqual(socket.sent[1]["data"], {"dashboard_id": "dashboard-1", "chart_id": "chart-1", "sql_text": "SELECT 1"})
        self.assertEqual(socket.sent[3]["data"]["chart_id"], "chart-1")
        session.preclose("finish")
        session.close()
        self.assertTrue(socket.closed)

    def test_invalid_frame_is_explicit_failure(self):
        for raw in ["not-json", b'{"message_type":"pong"}', '{"message_type":"error","data":{"status":"bad"}}', '{"message_type":"error","data":{"status":403,"msg":"fixture"}}', '{"message_type":"unknown"}']:
            with self.subTest(raw=raw):
                session = sdk.DashboardWebSocket(_Socket([raw]))
                with self.assertRaises(sdk.Error) as raised:
                    session.receive()
                self.assertEqual(raised.exception.code, "ErrResponseInvalid")

    def test_handshake_and_transport_failures(self):
        import websocket
        client = sdk.Client("https://fixture.test/newmoi", sdk.with_api_key("fixture"))
        refusal = {"code": "ErrForbidden", "msg": "localized fixture refusal"}
        for fault, code, status in [
            (websocket.WebSocketBadStatusException("fixture", status_code=403, resp_headers={"X-Request-ID": "handshake"}, resp_body=json.dumps(refusal)), refusal["code"], 403),
            (websocket.WebSocketBadStatusException("fixture", status_code=502, resp_headers={}, resp_body="not-json"), "ErrResponseInvalid", 502),
            (websocket.WebSocketTimeoutException("fixture"), "ErrTimeout", 0),
            (OSError("fixture"), "ErrTransportUnavailable", 0),
        ]:
            with self.subTest(code=code), patch("websocket.create_connection", side_effect=fault):
                with self.assertRaises(sdk.Error) as raised:
                    client.dashboard("ws").connect_web_socket()
                self.assertEqual((raised.exception.code, raised.exception.status), (code, status))
                if code == refusal["code"]:
                    self.assertEqual((raised.exception.message, raised.exception.request_id), (refusal["msg"], "handshake"))

    def test_real_websocket_ping_and_preview(self):
        from websockets.sync.server import serve

        self.enterContext(loopback_proxy_environment())
        received = []
        def handle(connection):
            for message_type, response_type in [("ping", "pong"), ("dashboard_preview_execute", "dashboard_preview_result")]:
                frame = json.loads(connection.recv())
                received.append(frame)
                if frame["message_type"] != message_type:
                    connection.close(code=1008)
                    return
                connection.send(json.dumps({"id": frame["id"], "message_type": response_type, "data": {"status": "success", "total": 1}}))

        server = serve(handle, "127.0.0.1", 0, subprotocols=["moi-api-key"])
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.socket.getsockname()[1]}/newmoi", sdk.with_api_key("fixture"))
        session = client.dashboard("ws").connect_web_socket()
        self.addCleanup(session.close)
        session.ping("heartbeat")
        self.assertEqual(session.receive().id, "heartbeat")
        session.preview_sql("preview", "d1", "", "SELECT 1")
        result = session.receive()
        self.assertEqual((result.id, result.data["status"]), ("preview", "success"))
        self.assertEqual(received[-1]["data"], {"dashboard_id": "d1", "chart_id": "", "sql_text": "SELECT 1"})
