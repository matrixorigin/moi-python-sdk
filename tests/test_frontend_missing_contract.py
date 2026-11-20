import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import moi_product_sdk as sdk


class FrontendMissingContractTest(unittest.TestCase):
    def setUp(self):
        self.client = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key"))

    def test_sandbox_administration_and_terminal_models(self):
        service = self.client.sandboxes("workspace")
        with patch.object(service, "_request", return_value={"items": [{"id": "sandbox", "workspace": {"id": "target", "owner_id": "owner", "account_name": "account"}}], "limit": 50, "offset": 0, "has_more": True}) as request:
            result = service.admin_list(sdk.with_query_param("workspace_id", "target"))
            request.assert_called_once_with("GET", "/admin/agent-sandboxes?workspace_id=target")
            self.assertEqual(result.items[0].workspace.account_name, "account")
            self.assertTrue(result.has_more)
        with patch.object(service, "_request", return_value={"id": "sandbox", "workspace": {"id": "target"}, "network_tools": ["git"]}) as request:
            result = service.admin_update_network("sandbox", sdk.SandboxNetworkRequest(network_tools=["git"]))
            request.assert_called_once_with("PATCH", "/admin/agent-sandboxes/sandbox/network", {"network_tools": ["git"]})
            self.assertEqual(result.workspace.id, "target")
        with patch.object(service, "_request", return_value={}) as request:
            service.admin_delete("sandbox")
            request.assert_called_once_with("DELETE", "/admin/agent-sandboxes/sandbox")
        with patch.object(service, "_request", return_value={"token": "signed-token", "expires_at": "2026-10-08T01:02:03Z"}) as request:
            result = service.terminal_token("sandbox")
            request.assert_called_once_with("GET", "/agent-sandboxes/sandbox/terminal")
            self.assertEqual((result.token, result.expires_at), ("signed-token", "2026-10-08T01:02:03Z"))
        with patch.object(service, "_request", return_value={"items": [{"id": "sandbox", "token_jti": "private"}]}), self.assertRaises(sdk.Error):
            service.admin_list()

    def test_agent_and_account_paths(self):
        agents = self.client.agents("workspace")
        with patch.object(agents, "_request", return_value={"executors": [{"id": "runner", "type": "runner", "connected_secs": 0, "connected": True, "ready": True}], "astra_reachable": True}) as request:
            health = agents.executor_health()
            request.assert_called_once_with("GET", "/agent-executors/health")
            self.assertTrue(health.executors[0].HasField("connected_secs"))
            self.assertTrue(health.astra_reachable)
        with patch.object(agents, "_request", return_value={"items": [{"id": "agent"}], "total": 1}) as request:
            self.assertEqual(agents.list(sdk.with_query_param("surface", "agent_chat"))["total"], 1)
            request.assert_called_once_with("GET", "/agents?surface=agent_chat")
        account = self.client.account()
        for path, action in (
            ("/user/me/registration-invite", account.registration_invite),
            ("/user/me/reward-center/items", account.reward_center_items),
            ("/user/me/reward-center/events?event_type=account.checkin+%26+reward", lambda: account.reward_center_events("account.checkin & reward")),
            ("/user/me/reward-center/invitations?page=2&page_size=10", lambda: account.reward_center_invitations("2", "10")),
        ):
            with self.subTest(path=path), patch.object(self.client, "_request", return_value={"id": "value"}) as request:
                self.assertEqual(action(), {"id": "value"})
                request.assert_called_once_with("GET", path)

    def test_stream_paths_and_bytes(self):
        agents, sql = self.client.agents("workspace"), self.client.sql("workspace")
        image, csv = io.BytesIO(b"image-bytes"), io.BytesIO(b"answer\n1\n")
        with patch.object(self.client, "_stream", return_value=image) as request:
            stream = agents.preview_query_visual("agent", "file")
            request.assert_called_once_with("GET", "/workspaces/workspace/agents/agent/query-visuals/file/preview", "workspace", None, accept="*/*")
            self.assertEqual(stream.read(), b"image-bytes")
            stream.close()
        with patch.object(self.client, "_stream", return_value=csv) as request:
            stream = sql.download_query_result("statement")
            request.assert_called_once_with("POST", "/query/result/download", "workspace", {"statement_id": "statement"}, accept="*/*")
            self.assertEqual(stream.read(), b"answer\n1\n")
            stream.close()

    def test_errors_preserve_public_envelope(self):
        actions = (
            lambda: self.client.sandboxes("workspace").admin_list(),
            lambda: self.client.sandboxes("workspace").admin_delete("sandbox"),
            lambda: self.client.sandboxes("workspace").admin_update_network("sandbox", sdk.SandboxNetworkRequest(network_tools=["git"])),
            lambda: self.client.sandboxes("workspace").terminal_token("sandbox"),
            lambda: self.client.agents("workspace").executor_health(),
            lambda: self.client.agents("workspace").list(),
            lambda: self.client.agents("workspace").preview_query_visual("agent", "file"),
            lambda: self.client.sql("workspace").download_query_result("statement"),
            self.client.account().registration_invite,
            self.client.account().reward_center_items,
            lambda: self.client.account().reward_center_events("account.checkin"),
            self.client.account().reward_center_invitations,
        )
        for action in actions:
            failure = urllib.error.HTTPError("http://localhost/newmoi", 403, "failure", {"X-Request-ID": "request-id"}, io.BytesIO(json.dumps({"code": "SANDBOX_FORBIDDEN", "msg": "无访问权限", "data": None}).encode()))
            with patch("urllib.request.urlopen", side_effect=failure), self.assertRaises(sdk.Error) as raised:
                action()
            self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id), (403, "SANDBOX_FORBIDDEN", "无访问权限", "request-id"))


if __name__ == "__main__":
    unittest.main()
