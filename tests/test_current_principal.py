import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


class CurrentPrincipalTest(unittest.TestCase):
    def test_compact_bootstrap_preserves_role_selection_and_resource_scope(self):
        client = sdk.Client("http://localhost/newmoi", sdk.with_token("token"))
        payload = {
            "user": "alice", "role": "analyst", "is_admin": False,
            "user_info": {"id": "u1", "name": "alice", "status": "enabled", "reserved": False},
            "iam_context": {
                "roles": [{"role_id": "10", "role_name": "analyst", "lifecycle_version": 4,
                           "selectable": True, "disabled_reason": ""}],
                "default_role_id": "10", "default_role_version": 3, "explicit_role_id": "10",
                "effective_role_id": "10", "role_context_status": "ready",
            },
            "iam_capabilities": {
                "effective_role_id": "10", "request_id": "req1", "trace_id": "trace1",
                "items": [{"capability_id": "action.model.update", "allowed": True, "reason_code": "ALLOW",
                           "all_resources": False, "resource_ids": ["llm:7"]}],
            },
            "iam_snapshot_version": "snapshot1",
        }
        with patch.object(client, "_request", return_value=payload):
            result = client.workspace_members("ws1").current_principal()
        self.assertIsInstance(result, sdk.CurrentWorkspacePrincipalResult)
        self.assertEqual(result.user_info.id, "u1")
        context = result.iam_context
        self.assertEqual(context.effective_role_id, "10")
        self.assertEqual(context.explicit_role_id, "10")
        self.assertEqual(context.default_role_version, 3)
        self.assertEqual(context.roles[0].role_id, "10")
        self.assertEqual(context.roles[0].lifecycle_version, 4)
        self.assertTrue(context.roles[0].selectable)
        capabilities = result.iam_capabilities
        self.assertEqual(capabilities.effective_role_id, context.effective_role_id)
        self.assertEqual((capabilities.request_id, capabilities.trace_id), ("req1", "trace1"))
        item = capabilities.items[0]
        self.assertEqual(item.capability_id, "action.model.update")
        self.assertTrue(item.allowed)
        self.assertFalse(item.all_resources)
        self.assertEqual(list(item.resource_ids), ["llm:7"])
        self.assertEqual(result.iam_snapshot_version, "snapshot1")
