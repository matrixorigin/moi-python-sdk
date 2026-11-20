import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


def export_task_list_options(body):
    options = []
    factories = {
        "keyword": sdk.with_export_task_keyword,
        "target_category": sdk.with_export_task_target_category,
        "limit": sdk.with_export_task_limit,
        "offset": sdk.with_export_task_offset,
        "connector_name": sdk.with_export_task_connector_name,
        "task_id": sdk.with_export_task_id,
        "order_by": sdk.with_export_task_order_by,
        "order_direction": sdk.with_export_task_order_direction,
        "creator": sdk.with_export_task_creator,
    }
    for key, factory in factories.items():
        if key in body:
            options.append(factory(body[key]))
    if body.get("statuses"):
        options.append(sdk.with_export_task_statuses(*body["statuses"]))
    return options


def export_task_files_options(body):
    options = []
    factories = {
        "limit": sdk.with_export_task_files_limit,
        "offset": sdk.with_export_task_files_offset,
        "order_by": sdk.with_export_task_files_order_by,
        "order_direction": sdk.with_export_task_files_order_direction,
    }
    for key, factory in factories.items():
        if key in body:
            options.append(factory(body[key]))
    if body.get("statuses"):
        options.append(sdk.with_export_task_file_statuses(*body["statuses"]))
    return options


class ConnectorOptionsHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        for fixture_name in ("connector_options_http_contract.json", "connector_core_http_contract.json", "connector_structured_http_contract.json", "connector_rest_http_contract.json", "import_export_lifecycle_http_contract.json"):
            fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / fixture_name
            for scenario in json.loads(fixture.read_text(encoding="utf-8")):
                with self.subTest(scenario=scenario["name"]):
                    self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=json.loads(raw) if raw else None,
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST
            do_PUT = do_POST
            do_DELETE = do_POST

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.connectors("workspace-1")
        input_value = scenario["input"]
        operation = scenario["operation"]
        result = None
        if operation == "preview-file":
            options = []
            if "conn_file_id" in input_value:
                options.append(sdk.with_connector_preview_conn_file_id(input_value["conn_file_id"]))
            if "sheet_name" in input_value:
                options.append(sdk.with_connector_preview_sheet_name(input_value["sheet_name"]))
            if "is_column_name" in input_value:
                options.append(sdk.with_connector_preview_column_name(input_value["is_column_name"]))
            if "row_start" in input_value:
                options.append(sdk.with_connector_preview_row_start(input_value["row_start"]))
            if "column_name_row" in input_value:
                options.append(sdk.with_connector_preview_column_name_row(input_value["column_name_row"]))
            if "csv" in input_value:
                csv = input_value["csv"]
                options.append(sdk.with_connector_preview_csv(csv["separator"], csv["delimiter"], csv["isEscape"]))
            if "file_type" in input_value:
                options.append(sdk.with_connector_preview_file_type(input_value["file_type"]))
            result = service.preview_file(input_value["connector_id"], input_value["uri"], *options)
            expected = json_format.ParseDict(scenario["response"]["data"], sdk.PreviewFileResult())
            self.assertEqual(result, expected)
        elif operation == "structured-source-capability":
            result = service.structured_source_capability(
                input_value["connector_id"], input_value["source_type"], input_value["database"], input_value["table"], input_value["schema"]
            )
            self.assertEqual(result.raw, scenario["response"]["data"])
            self.assertFalse(result.mysql_cdc_available)
            self.assertTrue(result.doris_flight_sql_read_available)
            self.assertFalse(result.doris_thrift_read_available)
            self.assertFalse(result.doris_jdbc_read_available)
            self.assertEqual(result.doris_read_mode, "flight_sql")
            self.assertEqual(result.doris_read_disabled_reasons, ["DORIS_THRIFT_READ_UNAVAILABLE"])
        elif operation == "probe-rest-draft":
            result = service.probe_rest_draft(input_value["config"])
        elif operation == "probe-rest":
            result = service.probe_rest(input_value["connector_id"])
        elif operation == "preview-rest":
            body = input_value["body"]
            request = sdk.RESTRequest(
                body["path"], body["method"],
                [sdk.RESTParameter(item["name"], item["value"]) for item in body.get("params", [])],
                [sdk.RESTParameter(item["name"], item["value"]) for item in body.get("headers", [])],
                body.get("json", ""),
                [sdk.RESTParameter(item["name"], item["value"]) for item in body.get("data", [])],
            )
            page = body["pagination"]
            preview = sdk.RESTPreview(
                request,
                sdk.RESTPagination(
                    page["type"], page.get("param", ""), page.get("start"), page.get("step", 0),
                    page.get("next_path", ""), page.get("total_path", ""),
                ),
                body.get("read_only_post", False), body.get("records_path", ""), body.get("schema_path", ""),
                body.get("schema_format", ""), body.get("cursor_param", ""), body.get("initial_cursor", ""),
            )
            result = service.preview_rest(input_value["connector_id"], preview)
        elif operation == "task-stats":
            result = service.task_stats()
        elif operation in ("tasks", "task-files"):
            options = [
                sdk.with_query_values(key, *values)
                for key, values in input_value.get("query_values", {}).items()
            ]
            result = service.tasks(*options) if operation == "tasks" else service.task_files(*options)
        elif operation == "update-task":
            body = input_value["body"]
            spec = sdk.ImportTaskUpdateSpec(
                body.get("LoadModeConfig"), name=body.get("Name", ""),
                file_filter_config=body.get("FileFilterConfig"), uris=body.get("URIs"),
            )
            result = service.update_task(input_value["task_id"], spec)
        elif operation == "create-task":
            body = input_value["body"]
            spec = sdk.ImportTaskCreateSpec(
                body["SourceConnectorID"], body["ConfigType"], body.get("SourceConfig"),
                structured_load_config=body.get("StructuredLoadConfig"), task_id=body.get("TaskID", ""),
            )
            options = []
            if "Name" in body:
                options.append(sdk.with_import_task_name(body["Name"]))
            if "VolumeID" in body:
                options.append(sdk.with_import_task_volume_id(body["VolumeID"]))
            result = service.create_task(spec, *options)
        elif operation == "create-export-task":
            body = scenario["request"]
            spec = sdk.ExportTaskCreateSpec(
                body["task_name"], body["connector_id"], body["connector_name"], body["type"],
                body["config"], body["files"], creator=body.get("creator", ""),
            )
            result = service.create_export_task(spec)
        elif operation == "export-tasks":
            result = service.export_tasks(*export_task_list_options(input_value.get("body", {})))
        elif operation == "export-task-files":
            result = service.export_task_files(
                input_value["task_id"], *export_task_files_options(input_value.get("body", {}))
            )
        elif operation in ("delete-task", "pause-task", "resume-task", "run-task-now", "run-task-full-refresh"):
            method = {
                "delete-task": service.delete_task,
                "pause-task": service.pause_task,
                "resume-task": service.resume_task,
                "run-task-now": service.run_task_now,
                "run-task-full-refresh": service.run_task_full_refresh,
            }[operation]
            result = method(input_value["task_id"])
        elif operation == "get-task":
            result = service.get_task(input_value["task_id"])
        elif operation == "task-runs":
            result = service.task_runs(input_value["task_id"])
        elif operation == "retry-task-files":
            result = service.retry_task_files(input_value["task_id"], *input_value["ids"])
        elif operation == "export-task-stats":
            result = service.export_task_stats()
        elif operation == "export-task-info":
            result = service.export_task_info(input_value["task_id"])
        elif operation == "delete-export-task":
            result = service.delete_export_task(input_value["task_id"])
        elif operation == "retry-export-task":
            result = service.retry_export_task(input_value["task_id"], *input_value["ids"])
        elif operation == "export-task-state":
            result = service.export_task_state(input_value["task_id"])
        elif operation == "structured-sources":
            result = service.structured_sources()
        elif operation == "structured-source-databases":
            result = service.structured_source_databases(input_value["connector_id"], input_value["source_type"])
        elif operation == "structured-source-schemas":
            result = service.structured_source_schemas(
                input_value["connector_id"], input_value["source_type"], input_value["database"]
            )
        elif operation == "structured-source-objects":
            body = input_value["body"]
            result = service.structured_source_objects(
                body["connector_id"], body["source_type"], body["database"], body.get("schema", "")
            )
        elif operation == "structured-source-schema":
            body = input_value["body"]
            source = body["source"]
            kafka_schema = None
            if "kafka_schema" in body:
                spec = body["kafka_schema"]
                sample = None
                if "sample" in spec:
                    value = spec["sample"]
                    sample = sdk.StructuredKafkaSampleSpec(
                        value["topic_mode"], value.get("topics"), value.get("topic_pattern", "")
                    )
                kafka_schema = sdk.StructuredKafkaSchemaSpec(
                    spec["key_format"], spec["value_format"], spec["schema_source"], spec.get("json_schema", ""),
                    sample, spec.get("sample_limit"),
                )
            result = service.structured_source_schema(
                body["connector_id"], source["source_type"], source.get("database", ""), source.get("table", ""),
                source.get("schema", ""), source.get("collection", ""), body.get("mongo_sample_limit"), kafka_schema,
            )
        elif operation == "structured-source-sample":
            body = input_value["body"]
            sample = body["kafka_sample"]
            result = service.structured_source_sample(
                body["connector_id"], body["source"]["source_type"], body["limit"], sample["topic_mode"],
                sample.get("topics"), sample.get("topic_pattern", ""),
            )
        elif operation == "structured-backfill-start-resolve":
            body = input_value["body"]
            source = body["source"]
            result = service.structured_backfill_start_resolve(
                body["connector_id"], source["source_type"], source.get("database", ""), source.get("table", ""),
                body["start_mode"], source.get("schema", ""), source.get("collection", ""), body.get("watermark"),
                body.get("custom_start_value"),
            )
        elif operation == "list":
            options = [sdk.with_query_param(key, value) for key, value in input_value["query_params"].items()]
            result = service.list(*options)
        elif operation == "get":
            result = service.get(input_value["connector_id"])
        elif operation in ("create", "validate"):
            options = []
            if input_value.get("config") is not None:
                options.append(sdk.with_connector_config(input_value["config"]))
            method = service.create if operation == "create" else service.validate
            result = method(input_value["name"], input_value["source_type"], input_value["usage_type"], *options)
        elif operation == "update":
            options = []
            if "name" in input_value:
                options.append(sdk.with_connector_name(input_value["name"]))
            if "source_type" in input_value:
                options.append(sdk.with_connector_source_type(input_value["source_type"]))
            if "usage_type" in input_value:
                options.append(sdk.with_connector_usage_type(input_value["usage_type"]))
            if input_value.get("config") is not None:
                options.append(sdk.with_connector_update_config(input_value["config"]))
            result = service.update(input_value["connector_id"], *options)
        elif operation == "delete":
            result = service.delete(input_value["connector_id"])
        elif operation == "db-list-databases":
            result = service.db_list_databases(input_value["connector_id"])
        elif operation == "db-list-schemas":
            result = service.db_list_schemas(input_value["connector_id"], input_value["database"])
        elif operation in ("db-list-tables", "db-source-schema"):
            options = [sdk.with_connector_schema(input_value["schema"])]
            if operation == "db-list-tables":
                result = service.db_list_tables(input_value["connector_id"], input_value["database"], *options)
            else:
                result = service.db_source_schema(
                    input_value["connector_id"], input_value["database"], input_value["table"], *options
                )
        elif operation == "mo-database-list":
            result = service.mo_database_list(input_value["connector_id"])
        elif operation == "mo-database-table-list":
            result = service.mo_database_table_list(input_value["connector_id"], input_value["database"])
        elif operation == "mo-check-table-name":
            result = service.mo_check_table_name(input_value["connector_id"], input_value["database"], input_value["table"])
        elif operation == "mo-column-mapping":
            result = service.mo_column_mapping(
                input_value["connector_id"], input_value["database"], input_value["table"], input_value["export_columns"]
            )
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        if operation in ("preview-file", "structured-source-capability"):
            return
        if operation.startswith("structured-"):
            self.assertEqual(result.raw, scenario["response"]["data"])
            if operation == "structured-source-schema":
                for field in ("mapping_draft", "target_type_catalog", "field_compatibilities"):
                    self.assertEqual(getattr(result, field), scenario["response"]["data"].get(field))
                for field in ("mapping_hash", "flatten_hash"):
                    self.assertEqual(getattr(result, field), scenario["response"]["data"].get(field, ""))
            return
        if operation in (
            "update", "delete", "update-task", "delete-task", "pause-task", "resume-task", "run-task-now",
            "run-task-full-refresh", "retry-task-files", "delete-export-task", "retry-export-task",
        ):
            self.assertIsNone(result)
            return
        result_types = {
            "list": sdk.ConnectorListResult,
            "get": sdk.Connector,
            "create": sdk.Connector,
            "validate": sdk.ConnectorValidateResult,
            "probe-rest-draft": sdk.ConnectorValidateResult,
            "probe-rest": sdk.ConnectorValidateResult,
            "preview-rest": sdk.RESTReadResult,
            "task-stats": sdk.ImportTaskStats,
            "create-task": sdk.ImportTaskCreateResult,
            "tasks": sdk.ImportTaskListResult,
            "get-task": sdk.ImportTaskInfoResult,
            "task-files": sdk.ImportTaskFileListResult,
            "task-runs": sdk.ImportTaskRunListResult,
            "export-task-stats": sdk.ExportTaskStats,
            "export-task-info": sdk.ExportTaskInfo,
            "export-task-state": sdk.ExportTaskStateResult,
            "create-export-task": sdk.ExportTask,
            "export-tasks": sdk.ExportTaskListResult,
            "export-task-files": sdk.ExportTaskFilesResult,
            "db-list-databases": sdk.DBListDatabasesResult,
            "db-list-schemas": sdk.DBListSchemasResult,
            "db-list-tables": sdk.DBListTablesResult,
            "db-source-schema": sdk.DBSourceSchemaResult,
            "mo-database-list": sdk.MODatabaseListResult,
            "mo-database-table-list": sdk.MODatabaseTableListResult,
            "mo-check-table-name": sdk.MOCheckTableNameResult,
            "mo-column-mapping": sdk.MOColumnMappingResult,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], result_types[operation]())
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
