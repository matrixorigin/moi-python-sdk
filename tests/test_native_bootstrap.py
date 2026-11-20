import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


class NativeBootstrapTest(unittest.TestCase):
    def test_native_bootstrap_preserves_typed_contract(self):
        client = sdk.Client("http://localhost/newmoi", sdk.with_token("native-token"))
        payload = {"issuer": "https://uc.example.test", "subject": "uc-user", "session_id": "session", "principal_id": "product-user", "catalog_user_id": "catalog-user", "workspaces": [{"id": "workspace", "status": "ACTIVE", "access_status": "accepted"}], "workspace_initialization": {"status": "ready"}}
        with patch.object(client, "_request", return_value=payload) as request:
            result = client.account().bootstrap_native()
            request.assert_called_once_with("POST", "/auth/cli/bootstrap", data_nullable=False)
        self.assertIsInstance(result, sdk.NativeBootstrapResult)
        self.assertEqual((result.principal_id, result.catalog_user_id), ("product-user", "catalog-user"))
        self.assertEqual(result.workspace_initialization.status, "ready")
