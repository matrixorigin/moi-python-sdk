import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# POST /workbook/list -> SQLWorkbookListResult strict-decode contract.
class SQLWorkbookListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "sql_workbook_list_report.json",
            "sql_workbook_list_adhoc.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._sql_workbook_list_result(
                    {
                        "total": 1,
                        "result": [self._fixture(name)],
                        "next_page_token": "",
                    }
                )
                self.assertEqual(len(result.result), 1)
                self.assertEqual(result.total, 1)
                workbook = result.result[0]
                self.assertTrue(workbook.workbook_id)
                self.assertTrue(workbook.name)

    def test_list_rejects_unknown_fields(self):
        workbook = self._fixture("sql_workbook_list_report.json")
        workbook["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._sql_workbook_list_result(
                {"total": 1, "result": [workbook]}
            )

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
