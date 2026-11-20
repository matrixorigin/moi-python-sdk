import unittest
from unittest.mock import patch
import moi_product_sdk as sdk


class ExportTaskStatsTest(unittest.TestCase):
    def test_stats_decodes_card_counts_and_uses_one_request(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).connectors("ws")
        counts = {"total": 22, "running": 10, "pending": 6, "failed": 4}
        with patch.object(service, "_request", return_value=counts) as request:
            result = service.export_task_stats()
        request.assert_called_once_with("GET", "/export/task/stats")
        self.assertIsInstance(result, sdk.ExportTaskStats)
        self.assertEqual((result.total, result.running, result.pending, result.failed), (22, 10, 6, 4))

    def test_list_passes_search_category_status_and_page(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).connectors("ws")
        with patch.object(service, "_connector_post", return_value={"tasks": [], "total": 0}) as request:
            service.export_tasks(sdk.with_export_task_keyword("资料"), sdk.with_export_task_target_category("storage"), sdk.with_export_task_statuses(0), sdk.with_export_task_limit(10), sdk.with_export_task_offset(20))
        request.assert_called_once_with("/export/task/list", {"keyword": "资料", "target_category": "storage", "statuses": [0], "limit": 10, "offset": 20})
