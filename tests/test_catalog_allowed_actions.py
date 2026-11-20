import unittest
from unittest.mock import Mock

from moi_product_sdk.client import CatalogService


class CatalogAllowedActionsContractTest(unittest.TestCase):
    def test_candidate_request_and_empty_actions(self):
        client = Mock()
        client._request.return_value = {
            "items": [{"resource_id": "10", "allowed_actions": []}]
        }
        service = CatalogService(client, "ws-1")
        result = service.allowed_actions("catalog", ["10"])
        client._request.assert_called_once_with(
            "POST", "/catalog/allowed-actions", "ws-1",
            {"resource_type": "catalog", "resource_ids": ["10"]}, False,
        )
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].resource_id, "10")
        self.assertEqual(list(result.items[0].allowed_actions), [])
