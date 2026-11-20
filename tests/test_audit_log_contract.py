import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# GET /audit/logs -> AuditLogListResult strict-decode contract.
class AuditLogListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "audit_log_success.json",
            "audit_log_failed.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._audit_log_list_result(
                    {
                        "items": [self._fixture(name)],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    }
                )
                self.assertEqual(len(result.items), 1)
                self.assertEqual(result.total, 1)
                self._assert_entry(result.items[0], name)

    def test_list_rejects_unknown_fields(self):
        entry = self._fixture("audit_log_success.json")
        entry["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._audit_log_list_result({"items": [entry], "total": 1})

    def _assert_entry(self, entry, fixture_name):
        self.assertTrue(entry.id)
        self.assertTrue(entry.workspace_id)
        self.assertTrue(entry.created_at)
        if fixture_name == "audit_log_success.json":
            self.assertEqual(entry.result, "success")
            self.assertEqual(entry.status_code, 200)
            self.assertEqual(entry.error_code, "")
            self.assertTrue(entry.request_id)
            self.assertEqual(entry.route_pattern, "/catalog/list")
        else:
            self.assertEqual(entry.result, "failed")
            self.assertEqual(entry.status_code, 403)
            self.assertEqual(entry.error_code, "ErrAccessDenied")
            self.assertTrue(entry.error_message)
            self.assertEqual(entry.request_body_json, "")

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
