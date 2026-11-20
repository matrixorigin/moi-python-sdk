import unittest
from unittest.mock import patch
import moi_product_sdk as sdk


class MysqlImportCapabilityTest(unittest.TestCase):
    def test_capability_preserves_proof_and_requires_an_actual_boolean(self):
        service = sdk.Client("http://localhost", sdk.with_api_key("key")).connectors("workspace")
        for value, expected in ((True, True), (False, False), (None, False)):
            with self.subTest(value=value), patch.object(service, "_connector_post", return_value={"mysql_cdc_available": value, "capability_profile_hash": "proof", "doris_cdc_available": False}) as request:
                result = service.structured_source_capability("connector", "mysql", "source", "items")
                self.assertIs(result.mysql_cdc_available, expected)
                self.assertEqual(result.capability_profile_hash, "proof")
                self.assertFalse(result.doris_cdc_available)
                self.assertEqual(request.call_args.args[0], "/connectors/structured/v1/source/capabilities")
        with patch.object(service, "_connector_post", return_value={"capability_profile_hash": "proof"}):
            self.assertFalse(service.structured_source_capability("connector", "mysql", "source", "items").mysql_cdc_available)

    def test_invalid_capability_type_is_a_protocol_failure(self):
        service = sdk.Client("http://localhost", sdk.with_api_key("key")).connectors("workspace")
        for value in ("true", 1, {}, []):
            with self.subTest(value=value), patch.object(service, "_connector_post", return_value={"mysql_cdc_available": value}), self.assertRaises(sdk.Error) as raised:
                service.structured_source_capability("connector", "mysql", "source", "items")
            self.assertEqual(raised.exception.code, "ErrResponseInvalid")
            self.assertIn("mysql_cdc_available", raised.exception.message)
