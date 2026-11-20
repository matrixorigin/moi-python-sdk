import io
import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


class Response(io.BytesIO):
    status = 200
    headers = {}

    def __init__(self):
        super().__init__(b'{"code":"OK","msg":"OK","data":{}}')


class CurrentRoleTest(unittest.TestCase):
    def test_validation_and_conflicts(self):
        for role in ("", "0", "-1", "+1", "01", " 1", "１", "9223372036854775808"):
            with self.subTest(role=role), self.assertRaises(sdk.Error) as caught:
                sdk.new_with_personal_access_token(
                    "http://backend", "pat", sdk.with_workspace_current_role_id("ws", role)
                )
            self.assertEqual(caught.exception.code, "ErrCurrentRoleInvalid")
        sdk.validate_current_role_id("9223372036854775807")
        with self.assertRaises(sdk.Error) as caught:
            sdk.new_with_personal_access_token(
                "http://backend",
                "pat",
                sdk.with_workspace_current_role_id("ws", "1"),
                sdk.with_workspace_current_role_id("ws", "2"),
            )
        self.assertEqual(caught.exception.code, "ErrWorkspaceCurrentRoleConflict")

    def test_all_transports_bind_scope_after_custom_headers(self):
        client = sdk.new_with_personal_access_token(
            "http://backend",
            "pat",
            sdk.with_workspace_current_role_id("ws", "42"),
            sdk.with_custom_header("x-moi-role-id", "99"),
            sdk.with_custom_header("X-WORKSPACE-ID", "wrong"),
        )
        for workspace, expected in (("ws", "42"), ("other", None), ("", None)):
            requests = []

            def send(request, **kwargs):
                requests.append({key.lower(): value for key, value in request.header_items()})
                return Response()

            with patch("urllib.request.urlopen", send), patch(
                "urllib.request.OpenerDirector.open", lambda _, req, **kw: send(req, **kw)
            ):
                client._request("GET", "/probe", workspace)
                client._stream("GET", "/probe", workspace).close()
                client._raw_request("POST", "/probe", workspace, b"{}", "application/json")
                client._raw_product_result("POST", "/probe", workspace, b"{}", "application/json")
                client._http_result(
                    "GET", "/probe", workspace_id=workspace, headers={"X-MOI-Role-ID": "98"}
                )
                client._product_result(
                    "GET", "/probe", workspace_id=workspace, headers={"X-MOI-Role-ID": "98"}
                )
                client._bytes_result("GET", "/probe", workspace_id=workspace)
            self.assertEqual(len(requests), 7)
            for headers in requests:
                self.assertEqual(headers.get("x-moi-role-id"), expected)
                self.assertEqual(headers.get("x-workspace-id"), workspace or None)
                self.assertEqual(headers.get("x-api-key"), "pat")
            headers = dict(
                value.split(": ", 1)
                for value in client.workspace(workspace or "other").sql().query_websocket_headers()
            )
            self.assertEqual(headers.get("X-MOI-Role-ID"), expected)
