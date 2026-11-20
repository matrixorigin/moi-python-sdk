import unittest
from unittest.mock import Mock

from moi_product_sdk.client import DashboardService


class DashboardSourceContractTest(unittest.TestCase):
    def test_get_preserves_source_availability_and_affected_charts(self):
        client = Mock()
        client._request.return_value = {
            "ID": "dashboard-1",
            "sources": [{
                "ID": "source-1",
                "DashboardID": "dashboard-1",
                "TableID": 42,
                "DatabaseName": "sales",
                "TableName": "orders",
                "Status": "invalid",
                "AffectedCharts": [{"ID": "chart-1", "Name": "Revenue"}],
            }],
        }
        dashboard = DashboardService(client, "ws-1").get("dashboard-1")
        client._request.assert_called_once_with(
            "GET", "/data-dashboards/dashboard-1", "ws-1", None, False,
        )
        self.assertEqual(len(dashboard.sources), 1)
        source = dashboard.sources[0]
        self.assertEqual(source.status, "invalid")
        self.assertEqual(len(source.affected_charts), 1)
        self.assertEqual(source.affected_charts[0].id, "chart-1")
        self.assertEqual(source.affected_charts[0].name, "Revenue")
