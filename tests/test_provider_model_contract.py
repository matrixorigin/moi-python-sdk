import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# Product SDK parses with json_format.ParseDict(ignore_unknown_fields=False).
# GET /models and GET /embedding/models share ProviderModel on the wire;
# every handler-emitted field must exist in the proto or list() raises
# ErrResponseInvalid (issue #19157).
class ProviderModelContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "models_list_chat_with_reasoning.json",
            "models_list_workspace_plain.json",
            "models_list_embedding_subtype.json",
        ):
            with self.subTest(fixture=name):
                model = self._fixture(name)
                result = sdk_client._provider_model_list_result({"models": [model]})
                self.assertEqual(len(result.models), 1)
                self._assert_model(result.models[0], name)

    def test_list_rejects_unknown_fields(self):
        model = self._fixture("models_list_chat_with_reasoning.json")
        model["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._provider_model_list_result({"models": [model]})

    def _assert_model(self, model, fixture_name):
        self.assertTrue(model.model)
        self.assertTrue(model.backend_name)
        if fixture_name == "models_list_chat_with_reasoning.json":
            self.assertEqual(len(model.reasoning_efforts), 5)
            self.assertEqual(model.reasoning_efforts[0], "none")
            self.assertEqual(model.reasoning_efforts[4], "max")
            self.assertEqual(model.source, "system")
            self.assertTrue(model.system_default)
        elif fixture_name == "models_list_workspace_plain.json":
            self.assertEqual(list(model.reasoning_efforts), [])
            self.assertEqual(model.source, "workspace")
            self.assertFalse(model.system_default)
        elif fixture_name == "models_list_embedding_subtype.json":
            self.assertEqual(model.model_type, "embedding")
            self.assertEqual(model.type, "embedding_multimodal")
            self.assertEqual(model.dim, 1024)

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
