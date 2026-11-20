import copy
import json
import pathlib
import unittest

from google.protobuf.json_format import MessageToDict

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# GET /connectors/list -> ConnectorListResult strict-decode contract.
class ConnectorListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "connector_list_mysql.json",
            "connector_list_s3_export.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._connector_list_result(
                    {"connectors": [self._fixture(name)], "total": 1}
                )
                self.assertEqual(len(result.connectors), 1)
                self.assertEqual(result.total, 1)
                self._assert_connector(result.connectors[0], name)

    def test_list_rejects_unknown_fields(self):
        connector = self._fixture("connector_list_mysql.json")
        connector["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._connector_list_result({"connectors": [connector], "total": 1})

    def _assert_connector(self, connector, fixture_name):
        self.assertTrue(connector.id)
        self.assertTrue(connector.name)
        if fixture_name == "connector_list_mysql.json":
            self.assertEqual(connector.source_type, 9)
            self.assertEqual(connector.status, "active")
            self.assertEqual(list(connector.usage_type), [1, 2])
            self.assertEqual(len(connector.related_task_ids), 2)
            self.assertEqual(connector.config["host"], "mysql.internal")
        else:
            self.assertEqual(connector.source_type, 5)
            self.assertEqual(connector.status, "failed")
            self.assertEqual(list(connector.usage_type), [2])
            self.assertEqual(list(connector.related_task_ids), [])
            self.assertEqual(connector.config["bucket"], "dw-archive")

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


class ConnectorValidationContractTest(unittest.TestCase):
    def test_validation_retains_false_and_distinguishes_missing_result(self):
        for payload in ({"valid": False}, {"valid": True}, {}):
            with self.subTest(payload=payload):
                result = sdk_client._connector_validate_result(payload)
                self.assertEqual(result.HasField("valid"), "valid" in payload)
                self.assertEqual(MessageToDict(result), payload)


if __name__ == "__main__":
    unittest.main()
