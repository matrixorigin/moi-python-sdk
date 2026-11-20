import unittest

from moi_product_sdk.client import WorkspaceHandle, WorkspaceService, with_query_param


class WorkspaceDeleteTest(unittest.TestCase):
    def test_delete_and_delete_result_preserve_wait_query(self):
        calls = []
        response = object()

        class Client:
            def workspaces(self):
                return WorkspaceService(self)

            def _request(self, method, path):
                calls.append((method, path))

            def _product_result(self, method, path):
                calls.append((method, path))
                return response

        client = Client()
        service = WorkspaceService(client)
        service.delete("workspace")
        service.delete("workspace", with_query_param("wait", "true"))
        self.assertIs(response, service.delete_result("workspace", with_query_param("wait", "true")))
        handle = WorkspaceHandle(client, "workspace")
        handle.delete()
        handle.delete(with_query_param("wait", "true"))
        self.assertEqual(
            [
                ("DELETE", "/workspaces/workspace"),
                ("DELETE", "/workspaces/workspace?wait=true"),
                ("DELETE", "/workspaces/workspace?wait=true"),
                ("DELETE", "/workspaces/workspace"),
                ("DELETE", "/workspaces/workspace?wait=true"),
            ],
            calls,
        )


if __name__ == "__main__":
    unittest.main()
