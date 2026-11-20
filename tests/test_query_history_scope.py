import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as client


class QueryHistoryScopeTest(unittest.TestCase):
    def test_categories_are_preserved_in_each_history_request(self):
        for scope in ("self", "workspace"):
            with self.subTest(scope=scope):
                overview = client._query_history_overview_body(
                    (sdk.with_query_history_overview_scope(scope),)
                )
                history = client._query_history_body(
                    (sdk.with_query_history_scope(scope), sdk.with_query_history_users("alice"))
                )
                record = client._query_record_body(
                    "statement-1", (sdk.with_query_record_scope(scope),)
                )
                self.assertEqual(overview["scope"], scope)
                self.assertEqual(history["scope"], scope)
                self.assertEqual(history["user"], ["alice"])
                self.assertEqual(record, {"statement_id": "statement-1", "scope": scope})

    def test_default_remains_the_backend_self_category(self):
        self.assertNotIn("scope", client._query_history_overview_body(()))
        self.assertNotIn("scope", client._query_history_body(()))
        self.assertNotIn("scope", client._query_record_body("statement-1", ()))


if __name__ == "__main__":
    unittest.main()
