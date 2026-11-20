import copy
import json
import pathlib
import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


_FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "workspace_member_deletion_failed.json"


class MemberDeletionContractTest(unittest.TestCase):
    def test_list_preserves_incomplete_deletion_and_diagnostics(self):
        with _FIXTURE.open(encoding="utf-8") as fixture:
            member = json.load(fixture)
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("admin-key")).workspace_members("workspace-1")
        cases = (
            member,
            {
                **member,
                "deletion": {
                    **member["deletion"],
                    "state": "pending",
                    "phase": "",
                    "code": "WORKSPACE_MEMBER_DELETE_PENDING",
                    "message": "Deletion has not finished. Continue deletion to check the result.",
                },
            },
            {key: value for key, value in {**member, "status": "enabled"}.items() if key != "deletion"},
        )
        for row in cases:
            with self.subTest(status=row["status"], deletion=row.get("deletion")), patch.object(
                service, "_request", return_value={"total": 1, "user_list": [copy.deepcopy(row)]}
            ) as request:
                result = service.members()
                request.assert_called_once_with("POST", "/user/list", {})
                decoded = result.user_list[0]
                self.assertEqual(decoded.iam_user_id, row["iam_user_id"])
                self.assertEqual(decoded.status, row["status"])
                self.assertEqual(decoded.HasField("deletion"), "deletion" in row)
                if "deletion" in row:
                    for field, value in row["deletion"].items():
                        self.assertEqual(getattr(decoded.deletion, field), value)


if __name__ == "__main__":
    unittest.main()
