import unittest
from unittest import mock

import moi_product_sdk as sdk


class CustomOperatorSourceTest(unittest.TestCase):
    def test_get_custom_operator_source_uses_identity_query(self):
        client = sdk.Client("http://example.test/newmoi", sdk.with_api_key("user-key"))
        workflows = client.workflows("ws-1")
        with mock.patch.object(
            workflows,
            "_request",
            return_value={
                "source": "package workflow",
                "origin": "draft",
                "node_id": "node-1",
                "version": "v1",
                "language": "go",
                "handler": "Run",
                "name": "Counter",
                "identifier": "counter",
            },
        ) as request:
            response = workflows.get_custom_operator_source(" node-1 ", " v1 ", " task-1 ")

        request.assert_called_once_with(
            "GET",
            "/workflow/v2/custom-operators/source?node_id=node-1&version=v1&task_id=task-1",
        )
        self.assertEqual(response.origin, "draft")
        self.assertEqual(response.node_id, "node-1")
        self.assertEqual(response.language, "go")


if __name__ == "__main__":
    unittest.main()
