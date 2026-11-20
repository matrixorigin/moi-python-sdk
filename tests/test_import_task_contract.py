import copy
import io
import urllib.error
import json
import pathlib
import unittest
from unittest.mock import patch

from google.protobuf import json_format

from moi_product_sdk.errors import Error

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


class ImportTaskContractTest(unittest.TestCase):
    def test_structured_task_create_uses_existing_sdk_transport(self):
        config = {"version": 1, "source": {"database": "orders", "table": "events"},
                  "load_policy": {"run_mode": "once", "conflict_policy": "fail"}}
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).connectors("ws")
        with patch.object(service, "_connector_post", return_value={"task_id": "task-1"}) as request:
            result = service.create_task(sdk.ImportTaskCreateSpec("connector-1", 3, structured_load_config=config))
        self.assertEqual(result.task_id, "task-1")
        request.assert_called_once_with("/task", {"source_connector_id": "connector-1", "config_type": 3,
                                                "structured_load_config": config})

    def test_task_list_passes_owner_filters_and_page(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).connectors("ws")
        with patch.object(service, "_request", return_value={"tasks": [], "total": 0}) as request:
            service.tasks(
                sdk.with_page(0), sdk.with_page_size(0), sdk.with_query_param("keyword", ""),
                sdk.with_query_param("order_by", "created_at"), sdk.with_query_param("is_desc", "false"),
                sdk.with_query_values("status", "0", "2"), sdk.with_query_values("connector_sources", "0", "17"),
                sdk.with_query_values("load_interval_types", "0", "4"), sdk.with_query_values("source_connector_ids", "", "connector/1"),
            )
        request.assert_called_once_with("GET", "/task/list?page=0&page_size=0&keyword=&order_by=created_at&is_desc=false&status=0&status=2&connector_sources=0&connector_sources=17&load_interval_types=0&load_interval_types=4&source_connector_ids=&source_connector_ids=connector%2F1")

    def test_task_list_preserves_parameter_error(self):
        message = "Invalid parameters. Please check and try again."
        failure = urllib.error.HTTPError("http://localhost/newmoi/task/list", 400, "Bad Request", {}, io.BytesIO(json.dumps({"code": "ErrParamInvalid", "msg": message}).encode()))
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key"), sdk.with_custom_header("Accept-Language", "en-US")).connectors("ws")
        with patch("urllib.request.urlopen", side_effect=failure) as request, self.assertRaises(Error) as raised:
            service.tasks(sdk.with_query_values("config_types", "0"))
        self.assertEqual(request.call_args.args[0].get_header("Accept-language"), "en-US")
        self.assertEqual((raised.exception.code, raised.exception.status, raised.exception.message), ("ErrParamInvalid", 400, message))

    def test_task_stats_uses_single_count_endpoint(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).connectors("ws")
        with patch.object(service, "_request", return_value={"total": 22, "running": 10, "waiting": 8, "failed": 4}) as request:
            result = service.task_stats()
        request.assert_called_once_with("GET", "/task/stats")
        self.assertIsInstance(result, sdk.ImportTaskStats)
        self.assertEqual((result.total, result.running, result.waiting, result.failed), (22, 10, 8, 4))

    def test_task_list_and_get_decode_complete_backend_fixtures_strictly(self):
        for fixture_name in (
            "issue13504_local_task.json",
            "issue13504_structured_task.json",
        ):
            task_value = self._fixture(fixture_name)
            cases = (
                (
                    "list",
                    lambda: sdk_client._import_task_list_result(
                        {"tasks": [task_value], "total": 1}
                    ).tasks[0],
                ),
                (
                    "get",
                    lambda: sdk_client._import_task_info_result(
                        {"task": task_value}
                    ).task,
                ),
            )
            for endpoint, decode in cases:
                with self.subTest(fixture=fixture_name, endpoint=endpoint):
                    self._assert_task(decode(), fixture_name)

    def test_task_list_and_get_reject_unknown_fields(self):
        task_value = self._fixture("issue13504_local_task.json")
        task_value["unregistered_field"] = True
        cases = (
            lambda: sdk_client._import_task_list_result(
                {"tasks": [task_value], "total": 1}
            ),
            lambda: sdk_client._import_task_info_result({"task": task_value}),
        )
        for decode in cases:
            with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
                decode()

    def _assert_task(self, task, fixture_name):
        self.assertNotEqual(task.config_type, 0)
        self.assertEqual(task.total_rows, 4)
        self.assertNotEqual(task.imported_rows, 0)
        self.assertEqual(task.target_path_state, "resolved")
        for stats in (task.latest_rows, task.cumulative_rows):
            self.assertTrue(stats.HasField("read_rows"))
            self.assertTrue(stats.HasField("succeeded_rows"))
            self.assertTrue(stats.HasField("failed_rows"))
            self.assertTrue(stats.HasField("skipped_rows"))
            self.assertEqual(stats.failed_rows, 0)
            self.assertTrue(stats.complete)

        if fixture_name == "issue13504_local_task.json":
            self.assertEqual(task.config_type, 1)
            self.assertEqual(task.error_code, "LOCAL_IMPORT_EXECUTION_FAILED")
            self.assertEqual(len(task.source_files), 2)
            for source_file, filename in zip(
                task.source_files, ("orders.csv", "orders-2.csv")
            ):
                self.assertEqual(len(source_file.values), 2)
                for value in source_file.values:
                    self.assertEqual(value.WhichOneof("kind"), "string_value")
                self.assertEqual(
                    source_file.values[0].string_value, task.connector_name
                )
                self.assertEqual(source_file.values[1].string_value, filename)
            encoded = json_format.MessageToDict(
                task, preserving_proto_field_name=True
            )
            self.assertEqual(
                encoded["source_files"],
                [
                    ["local", "orders.csv"],
                    ["local", "orders-2.csv"],
                ],
            )
            self.assertNotIn("values", json.dumps(encoded["source_files"]))
            return

        self.assertEqual(task.config_type, 3)
        self.assertEqual(task.error_code, "")
        summary = json_format.MessageToDict(
            task.structured_load_summary, preserving_proto_field_name=True
        )
        runtime = json_format.MessageToDict(
            task.structured_runtime, preserving_proto_field_name=True
        )
        for field in ("source", "target", "progress", "checkpoint", "reconcile"):
            self.assertIn(field, summary)
        for field in ("progress", "checkpoint", "reconcile", "last_run"):
            self.assertIn(field, runtime)

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
