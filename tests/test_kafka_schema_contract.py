import unittest
from unittest.mock import Mock

from moi_product_sdk import (
    StructuredKafkaSampleSpec,
    StructuredKafkaSchemaSpec,
)
from moi_product_sdk.client import ConnectorService, ErrDatabaseRequired


class KafkaSchemaContractTest(unittest.TestCase):
    def test_provided_schema_without_database_preserves_options(self):
        client = Mock()
        client._request.return_value = {"schema_snapshot": {"columns": []}}
        connectors = ConnectorService(client, "workspace")
        schema = StructuredKafkaSchemaSpec("binary", "json", "provided", '{"type":"object"}')
        connectors.structured_source_schema("connector", "SOURCE_TYPE_KAFKA", kafka_schema=schema)
        self.assertEqual(client._request.call_args.args[1], "/connectors/structured/v1/source/schema")
        self.assertEqual(client._request.call_args.args[3]["kafka_schema"], {
            "key_format": "binary", "value_format": "json", "schema_source": "provided",
            "json_schema": '{"type":"object"}',
        })

    def test_sample_schema_preserves_topic_scope(self):
        client = Mock()
        client._request.return_value = {"schema_snapshot": {"columns": []}}
        connectors = ConnectorService(client, "workspace")
        schema = StructuredKafkaSchemaSpec("string", "json", "sample",
            sample=StructuredKafkaSampleSpec("pattern", topic_pattern="orders-.*"), sample_limit=20)
        connectors.structured_source_schema("connector", "SOURCE_TYPE_KAFKA", kafka_schema=schema)
        self.assertEqual(client._request.call_args.args[3]["kafka_schema"], {
            "key_format": "string", "value_format": "json", "schema_source": "sample",
            "sample": {"topic_mode": "pattern", "topic_pattern": "orders-.*"}, "sample_limit": 20,
        })

    def test_database_source_still_requires_database(self):
        client = Mock()
        connectors = ConnectorService(client, "workspace")
        with self.assertRaises(type(ErrDatabaseRequired)):
            connectors.structured_source_schema("connector", "SOURCE_TYPE_MYSQL")
        client._request.assert_not_called()
