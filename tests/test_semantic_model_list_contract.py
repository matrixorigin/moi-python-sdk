import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# GET /semantic-models -> SemanticModelListResult strict-decode contract.
class SemanticModelListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "semantic_model_list_knowledge.json",
            "semantic_model_list_empty.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._semantic_model_list_result(
                    {"items": [self._fixture(name)], "total": 1}
                )
                self.assertEqual(len(result.items), 1)
                self.assertEqual(result.total, 1)
                self._assert_model(result.items[0], name)

    def test_list_decodes_next_page_token(self):
        model = self._fixture("semantic_model_list_knowledge.json")
        result = sdk_client._semantic_model_list_result(
            {"items": [model], "total": 12, "next_page_token": "tok-2"}
        )
        self.assertEqual(result.next_page_token, "tok-2")

    def test_list_rejects_unknown_fields(self):
        model = self._fixture("semantic_model_list_knowledge.json")
        model["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._semantic_model_list_result({"items": [model], "total": 1})

    def _assert_model(self, model, fixture_name):
        self.assertNotEqual(model.id, 0)
        self.assertTrue(model.name)
        if fixture_name == "semantic_model_list_knowledge.json":
            self.assertEqual(list(model.allowed_actions), ["semantic_model.delete", "semantic_model.update", "semantic_model.use"])
            self.assertEqual(model.semantic_model_kind, "drawing")
            self.assertTrue(model.drawing_structured_enabled)
            self.assertEqual(model.drawing_number_policy, "keep_versions")
            self.assertFalse(model.can_append_sources)
            self.assertTrue(model.can_write)
            self.assertEqual(len(model.tables.list_value.values), 2)
            self.assertEqual(len(model.files.list_value.values), 1)
            self.assertEqual(model.source_counts.total, 3)
        else:
            self.assertEqual(list(model.allowed_actions), [])
            self.assertFalse(model.can_write)
            self.assertEqual(model.description, "")
            self.assertEqual(model.source_counts.total, 0)

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
