import unittest
from unittest.mock import patch

import moi_product_sdk as sdk
from moi_product_sdk.sandbox import SandboxQuotaRequest


class SandboxContractTest(unittest.TestCase):
    def test_quota_network_capabilities_require_an_explicit_query(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).sandboxes("workspace")
        legacy = {"current": 0, "limit": 2, "default_egress_endpoints": []}
        with patch.object(service, "_request", return_value=legacy) as transport:
            self.assertFalse(service.get_quota().HasField("unrestricted_network_allowed"))
            transport.assert_called_once_with("GET", "/agent-sandboxes/quota")
        expanded = {**legacy, "unrestricted_network_allowed": True}
        with patch.object(service, "_request", return_value=expanded) as transport:
            result = service.get_quota(sdk.with_query_param("include_network_capabilities", "true"))
            self.assertTrue(result.HasField("unrestricted_network_allowed"))
            self.assertTrue(result.unrestricted_network_allowed)
            transport.assert_called_once_with("GET", "/agent-sandboxes/quota?include_network_capabilities=true")

    def test_admin_detail_quota_and_ssh_contracts(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).sandboxes("workspace")
        with patch.object(service, "_request", return_value={"id": "sandbox", "workspace": {"id": "target"}}) as transport:
            self.assertEqual(service.admin_get("sandbox").workspace.id, "target")
            transport.assert_called_once_with("GET", "/admin/agent-sandboxes/sandbox")
        with patch.object(service, "_request", return_value={"workspace_id": "target", "max_managed_count": 0}) as transport:
            self.assertEqual(service.admin_update_quota("target", SandboxQuotaRequest(max_managed_count=0)).workspace_id, "target")
            transport.assert_called_once_with("PATCH", "/admin/workspaces/target/sandbox-quota", {"max_managed_count": 0})
        with patch.object(service, "_request", return_value={"token": "session", "gateway_host": "127.0.0.1", "gateway_port": 2222, "expires_at_ms": 1791763200000}) as transport:
            session = service.create_ssh_session("sandbox")
            self.assertEqual(session.gateway_port, 2222)
            self.assertEqual(session.expires_at_ms, 1791763200000)
            transport.assert_called_once_with("POST", "/agent-sandboxes/sandbox/ssh-session")

    def test_quota_update_preserves_explicit_zero_and_omission(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).sandboxes("workspace")
        request = SandboxQuotaRequest(max_managed_count=0, auto_ephemeral="inherit")
        with patch.object(service, "_request", return_value={"workspace_id": "workspace", "max_managed_count": 0, "max_ephemeral_count": 10}) as transport:
            result = service.update_quota(request)
            transport.assert_called_once_with("PATCH", "/agent-sandboxes/quota", {"max_managed_count": 0, "auto_ephemeral": "inherit"})
            self.assertEqual(result.max_ephemeral_count, 10)

    def test_update_availability_preserves_unknown(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).sandboxes("workspace")
        for value in (None, False, True):
            with self.subTest(value=value), patch.object(service, "_request", return_value={"id": "sandbox", "update_available": value}):
                result = service.get("sandbox")
                self.assertEqual(result.HasField("update_available"), value is not None)
                self.assertEqual(result.update_available, bool(value))

    def test_list_rejects_internal_field_or_wrong_shape(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).sandboxes("workspace")
        for data in ([{"id": "sandbox", "token_jti": "private"}], {"sandboxes": []}):
            with self.subTest(data=data), patch.object(service, "_request", return_value=data), self.assertRaises(sdk.Error):
                service.list()


if __name__ == "__main__":
    unittest.main()
