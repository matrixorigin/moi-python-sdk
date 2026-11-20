import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class CatalogFolderHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        for fixture_name in ("catalog_folder_http_contract.json", "catalog_info_http_contract.json", "catalog_data_asset_http_contract.json", "catalog_table_http_contract.json", "catalog_file_http_contract.json", "catalog_core_http_contract.json"):
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
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    body=json.loads(raw) if raw else None,
                )
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.catalog("workspace-1")
        input_value = scenario["input"]
        operation = scenario["operation"]

        def invoke():
            if operation == "create-folder":
                options = []
                if "description" in input_value:
                    options.append(sdk.with_folder_description(input_value["description"]))
                return service.create_folder(
                    input_value["parent_volume_id"], input_value["database_id"], input_value["name"], *options
                )
            if operation == "update-folder":
                options = []
                if "name" in input_value:
                    options.append(sdk.with_folder_name(input_value["name"]))
                if "description" in input_value:
                    options.append(sdk.with_updated_folder_description(input_value["description"]))
                return service.update_folder(input_value["folder_id"], *options)
            if operation == "delete-folder":
                return service.delete_folder(input_value["folder_id"])
            if operation == "clean-folder":
                return service.clean_folder(input_value["folder_id"])
            if operation in ("create", "create-database", "create-volume", "update", "update-database-description", "update-volume"):
                options = []
                if "description" in input_value:
                    options.append(sdk.with_catalog_description(input_value["description"]))
                if operation == "create":
                    return service.create(input_value["name"], *options)
                if operation == "create-database":
                    return service.create_database(input_value["catalog_id"], input_value["name"], *options)
                if operation == "create-volume":
                    return service.create_volume(input_value["database_id"], input_value["name"], *options)
                if operation == "update":
                    return service.update(input_value["catalog_id"], input_value["name"], *options)
                if operation == "update-database-description":
                    return service.update_database_description(input_value["database_id"], *options)
                return service.update_volume(input_value["volume_id"], input_value["name"], *options)
            if operation == "data-asset":
                return service.data_asset(input_value["asset_id"])
            if operation == "batch-get-data-assets":
                return service.batch_get_data_assets(*input_value["raw_file_ids"])
            if operation == "file-data-asset":
                return service.file_data_asset(input_value["file_id"])
            if operation == "file-artifact":
                return service.file_artifact(input_value["file_id"])
            if operation == "batch-resolve-file-artifacts":
                return service.batch_resolve_file_artifacts(*input_value["file_ids"])
            if operation == "create-table":
                columns = [
                    sdk.TableColumn(
                        column["name"], column["type"],
                        is_pk=column.get("is_pk"), comment=column.get("comment", ""),
                        precision=column.get("precision"), default=column.get("default") if "default" in column else None,
                    )
                    for column in input_value["columns"]
                ]
                options = []
                if "comment" in input_value:
                    options.append(sdk.with_table_comment(input_value["comment"]))
                if "data_file_url" in input_value:
                    options.append(sdk.with_table_data_file_url(input_value["data_file_url"]))
                for option in input_value.get("column_load_options", []):
                    options.append(sdk.with_column_load_option(option["column"], option["data_from"]))
                return service.create_table_from_columns(input_value["database_id"], input_value["name"], columns, *options)
            if operation == "table-info":
                options = []
                if "name" in input_value:
                    options.append(sdk.with_table_lookup_name(input_value["name"]))
                if "database_id" in input_value:
                    options.append(sdk.with_table_lookup_database_id(input_value["database_id"]))
                if "database_name" in input_value:
                    options.append(sdk.with_table_lookup_database_name(input_value["database_name"]))
                if "include_stats" in input_value:
                    options.append(sdk.with_table_lookup_include_stats(input_value["include_stats"]))
                return service.table_info(input_value["table_id"], *options)
            if operation in ("table-data", "preview-table"):
                options = []
                option_factories = {
                    "page": sdk.with_table_data_page,
                    "page_size": sdk.with_table_data_page_size,
                    "name": sdk.with_table_data_name,
                    "database_id": sdk.with_table_data_database_id,
                    "database_name": sdk.with_table_data_database_name,
                    "preview_lines": sdk.with_table_preview_lines,
                    "include_total": sdk.with_table_data_include_total,
                }
                for name, factory in option_factories.items():
                    if name in input_value:
                        options.append(factory(input_value[name]))
                method = service.table_data if operation == "table-data" else service.preview_table
                return method(input_value["table_id"], *options)
            if operation == "files":
                options = [
                    sdk.with_file_list_filter("file_ext", *input_value["extensions"]),
                    sdk.with_file_list_filter("file_ids", *input_value["file_ids"]),
                    sdk.with_file_list_filter("file_type", input_value["file_type"]),
                    sdk.with_fuzzy_file_list_filter("file_name", True, input_value["name"]),
                    sdk.with_file_list_filter("parent_id", input_value["parent_id"]),
                    sdk.with_file_list_filter("volume_id", input_value["volume_key"]),
                    sdk.with_file_list_page(input_value["page"]),
                    sdk.with_file_list_page_size(input_value["page_size"]),
                    sdk.with_file_list_order(input_value["order"]),
                    sdk.with_file_list_order_by(input_value["order_by"]),
                ]
                return service.files(*options)
            if operation == "create-file":
                return service.create_file(input_value["volume_id"], *input_value["file_ids"])
            if operation == "file-info":
                return service.file_info(input_value["file_id"])
            if operation == "delete-file":
                return service.delete_file(input_value["file_id"], input_value["volume_key"])
            if operation == "delete-file-ref":
                return service.delete_file_ref(input_value["volume_id"], *input_value["file_ids"])
            if operation == "trigger-file-workflow":
                return service.trigger_file_workflow(input_value["volume_id"], *input_value["file_ids"])
            if operation == "multi-table-info":
                return service.multi_table_info(*input_value["table_ids"])
            if operation == "delete-table":
                return service.delete_table(input_value["table_id"])
            if operation == "table-exists":
                return service.table_exists(input_value["database_id"], input_value["name"])
            if operation == "table-full-path":
                return service.table_full_path(input_value["table_id"])
            if operation == "truncate-table":
                return service.truncate_table(input_value["table_id"])
            if operation == "table-overview":
                return service.table_overview(input_value["database_id"])
            if operation == "health":
                return service.health()
            if operation == "allowed-actions":
                return service.allowed_actions(input_value["resource_type"], input_value["resource_ids"])
            if operation in ("list", "list-databases", "database-children"):
                options = []
                if "include_stats" in input_value:
                    options.append(sdk.with_catalog_include_stats(input_value["include_stats"]))
                if "page_size" in input_value:
                    options.append(sdk.with_catalog_page_size(input_value["page_size"]))
                if "page_token" in input_value:
                    options.append(sdk.with_catalog_page_token(input_value["page_token"]))
                if operation == "list":
                    return service.list(*options)
                if operation == "list-databases":
                    return service.list_databases(input_value["catalog_id"], *options)
                return service.database_children(input_value["database_id"], *options)
            if operation == "info":
                return service.info(input_value["catalog_id"])
            if operation == "delete":
                return service.delete(input_value["catalog_id"])
            if operation == "run-nl2sql":
                return service.run_nl2sql(input_value["database_id"], input_value["sql"])
            if operation == "database-info":
                return service.database_info(input_value["database_id"])
            if operation == "delete-database":
                return service.delete_database(input_value["database_id"])
            if operation == "volume-info":
                return service.volume_info(input_value["volume_key"])
            if operation == "delete-volume":
                return service.delete_volume(input_value["volume_id"])
            if operation == "volume-full-path":
                return service.volume_full_path(input_value["volume_id"])
            if operation.endswith("-references"):
                method = {
                    "catalog-references": service.catalog_references,
                    "database-references": service.database_references,
                    "volume-references": service.volume_references,
                    "folder-references": service.folder_references,
                    "table-references": service.table_references,
                }[operation]
                return method(input_value["id"])
            if operation == "list-workspace-files":
                options = [
                    sdk.with_page_size(input_value["page_size"]),
                    sdk.with_page_token(input_value["page_token"]),
                    sdk.with_query_param("filter_file_name_fuzzy", input_value["name"]),
                ]
                options.extend(sdk.with_query_values("filter_file_id", value) for value in input_value["file_ids"])
                options.extend(sdk.with_query_values("filter_file_ext", value) for value in input_value["extensions"])
                return service.list_workspace_files(*options)
            if operation == "workspace-file-model-url":
                return service.workspace_file_model_url(input_value["file_id"])
            self.fail(f"unknown operation {operation}")

        result = None
        if scenario["status"] >= 400:
            with self.assertRaises(sdk.Error) as caught:
                invoke()
            error = caught.exception
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            result = invoke()

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertEqual(observed["body"], scenario["request"])
        if result is not None:
            result_types = {
                "create-folder": sdk.CreateFolderResult,
                "data-asset": sdk.CatalogDataAssetResolveResult,
                "file-data-asset": sdk.CatalogDataAssetResolveResult,
                "batch-get-data-assets": sdk.CatalogBatchGetDataAssetsResult,
                "file-artifact": sdk.CatalogFileArtifactResult,
                "batch-resolve-file-artifacts": sdk.CatalogBatchResolveFileArtifactsResult,
                "create-table": sdk.CatalogCreateTableResult,
                "table-info": sdk.CatalogTableInfoResult,
                "table-data": sdk.CatalogTableDataResult,
                "preview-table": sdk.CatalogTableDataResult,
                "files": sdk.CatalogFileListResult,
                "file-info": sdk.FileInfoResult,
                "trigger-file-workflow": sdk.TriggerFileWorkflowResult,
                "multi-table-info": sdk.CatalogMultiTableInfoResult,
                "table-exists": sdk.BoolDataResult,
                "table-full-path": sdk.PathResult,
                "table-overview": sdk.CatalogTableOverviewResult,
                "health": sdk.HealthResult,
                "allowed-actions": sdk.CatalogAllowedActionsResult,
                "list": sdk.CatalogListResult,
                "info": sdk.CatalogInfoResult,
                "run-nl2sql": sdk.CatalogNL2SQLRunResult,
                "list-databases": sdk.DatabaseListResult,
                "database-info": sdk.DatabaseInfoResult,
                "database-children": sdk.DatabaseChildrenResult,
                "volume-info": sdk.VolumeInfoResult,
                "volume-full-path": sdk.PathResult,
                "catalog-references": sdk.RefListResult,
                "database-references": sdk.RefListResult,
                "volume-references": sdk.RefListResult,
                "folder-references": sdk.RefListResult,
                "table-references": sdk.RefListResult,
                "list-workspace-files": sdk.WorkspaceFileListResult,
                "workspace-file-model-url": sdk.URLResult,
            }
            expected_type = result_types.get(operation, sdk.IDResult)()
            expected = json_format.ParseDict(scenario["response"]["data"], expected_type)
            self.assertEqual(result, expected)
        elif scenario["status"] < 400:
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
