import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# POST /catalog/list -> CatalogListResult strict-decode contract.
class CatalogListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "catalog_list_full.json",
            "catalog_list_system_reserved.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._catalog_list_result(
                    {"list": [self._fixture(name)]}
                )
                self.assertEqual(len(result.list), 1)
                self._assert_catalog(result.list[0], name)

    def test_list_rejects_unknown_fields(self):
        catalog = self._fixture("catalog_list_full.json")
        catalog["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._catalog_list_result({"list": [catalog]})

    def _assert_catalog(self, catalog, fixture_name):
        self.assertNotEqual(catalog.id, 0)
        self.assertTrue(catalog.name)
        if fixture_name == "catalog_list_full.json":
            self.assertFalse(catalog.reserved)
            self.assertEqual(catalog.display_name, "Retail Warehouse")
            self.assertEqual(catalog.table_count, 56)
            self.assertEqual(len(catalog.allowed_actions), 2)
            self.assertTrue(catalog.created_by)
            self.assertTrue(catalog.updated_by)
        else:
            self.assertTrue(catalog.reserved)
            self.assertEqual(catalog.display_name, "")
            self.assertEqual(catalog.volume_count, 0)
            self.assertEqual(list(catalog.allowed_actions), ["catalog.read"])

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
