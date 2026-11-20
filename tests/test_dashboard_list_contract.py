import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# POST /data-dashboards/list -> DataDashboardListResult strict-decode contract.
# The dashboard family uses PascalCase json names on the wire.
class DashboardListContractTest(unittest.TestCase):
    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "dashboard_list_full.json",
            "dashboard_list_bare.json",
        ):
            with self.subTest(fixture=name):
                result = self._decode(
                    {"items": [self._fixture(name)], "total": 1, "has_more": False}
                )
                self.assertEqual(len(result.items), 1)
                self.assertEqual(result.total, 1)
                self._assert_dashboard(result.items[0], name)

    def test_list_rejects_unknown_fields(self):
        dashboard = self._fixture("dashboard_list_bare.json")
        dashboard["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            self._decode({"items": [dashboard], "total": 1})

    def _assert_dashboard(self, dashboard, fixture_name):
        self.assertTrue(dashboard.id)
        self.assertTrue(dashboard.name)
        self.assertTrue(dashboard.created_at)
        if fixture_name == "dashboard_list_full.json":
            self.assertEqual(len(dashboard.sources), 1)
            self.assertEqual(dashboard.sources[0].table_name, "fact_sales")
            self.assertEqual(dashboard.sources[0].status, "active")
            self.assertEqual(len(dashboard.sources[0].affected_charts), 1)
            self.assertEqual(len(dashboard.charts), 1)
            self.assertTrue(dashboard.charts[0].alert_enabled)
            self.assertEqual(len(dashboard.alerts), 1)
            self.assertEqual(dashboard.active_alert_count, 1)
        else:
            self.assertEqual(dashboard.lifecycle_status, "deleting")
            self.assertEqual(len(dashboard.sources), 0)
            self.assertEqual(len(dashboard.charts), 0)
            self.assertEqual(len(dashboard.alerts), 0)
            self.assertEqual(dashboard.active_alert_count, 0)

    def _decode(self, data):
        return sdk_client._product_message(
            data, sdk.DataDashboardListResult(), "dashboard data"
        )

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
