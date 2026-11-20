import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# GET /workspaces -> WorkspaceListResult strict-decode contract.
class WorkspaceListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "workspace_list_owner.json",
            "workspace_list_pending_invite.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._workspace_list_result(
                    {"workspaces": [self._fixture(name)], "total": 1}
                )
                self.assertEqual(len(result.workspaces), 1)
                self.assertEqual(result.total, 1)
                self._assert_workspace(result.workspaces[0], name)

    def test_list_rejects_unknown_fields(self):
        workspace = self._fixture("workspace_list_owner.json")
        workspace["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._workspace_list_result({"workspaces": [workspace], "total": 1})

    def _assert_workspace(self, workspace, fixture_name):
        self.assertTrue(workspace.id)
        self.assertTrue(workspace.name)
        self.assertTrue(workspace.created_at)
        if fixture_name == "workspace_list_owner.json":
            self.assertEqual(workspace.status, "ACTIVE")
            self.assertEqual(workspace.access_status, "accepted")
            self.assertTrue(workspace.owner_name)
            self.assertTrue(workspace.owner_email)
            self.assertEqual(workspace.invitation_id, "")
        else:
            self.assertEqual(workspace.status, "PENDING_INVITATION")
            self.assertEqual(workspace.access_status, "pending")
            self.assertTrue(workspace.invitation_id)
            self.assertEqual(workspace.owner_name, "")
            self.assertEqual(workspace.owner_email, "")

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
