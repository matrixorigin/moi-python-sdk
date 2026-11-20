import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# POST /catalog/file/list -> CatalogFileListResult strict-decode contract.
class CatalogFileListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "catalog_file_document.json",
            "catalog_file_folder.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._catalog_file_list_result(
                    {"total": 1, "list": [self._fixture(name)]}
                )
                self.assertEqual(len(result.list), 1)
                self.assertEqual(result.total, 1)
                self._assert_file(result.list[0], name)

    def test_list_rejects_unknown_fields(self):
        item = self._fixture("catalog_file_document.json")
        item["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._catalog_file_list_result({"total": 1, "list": [item]})

    def _assert_file(self, item, fixture_name):
        self.assertTrue(item.id)
        self.assertTrue(item.name)
        self.assertTrue(item.created_at)
        if fixture_name == "catalog_file_document.json":
            self.assertEqual(item.file_type, "file")
            self.assertEqual(item.workflow_role, "input")
            self.assertEqual(item.size, 5242880)
            self.assertEqual(item.parsed_file_id, "file-6002")
            self.assertFalse(item.volume_reserved)
        else:
            self.assertEqual(item.file_type, "folder")
            self.assertEqual(item.size, 0)
            self.assertEqual(item.workflow_role, "")
            self.assertTrue(item.volume_reserved)
            self.assertEqual(item.ref_workflow_id, "")

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
