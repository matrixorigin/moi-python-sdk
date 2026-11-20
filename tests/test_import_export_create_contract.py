import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


_FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "import_export_create_contract.json"


class ImportExportCreateContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())
        self.fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        self.requests = []
        self.status = 200
        self.response = {}
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                test.requests.append((self.command, self.path, self.headers.get("X-Workspace-ID"), body))
                payload = json.dumps(test.response, ensure_ascii=False).encode("utf-8")
                self.send_response(test.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(self.server.shutdown)
        self.client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))

    def test_file_import_optional_fields_and_owner_errors(self):
        # The owner supplies an absent task name and accepts an absent volume;
        # the SDK must not invent either value or reject this valid request.
        for case in self.fixture["file_imports"]:
            for denied in (False, True):
                with self.subTest(case=case["name"], denied=denied):
                    self.requests.clear()
                    body = case["request"]
                    common = body["source_config"]["common_file_task_config"]
                    spec = sdk.FileImportTaskSpec(
                        body["config_type"], common["uris"], common["load_mode_config"], common["file_filter_config"],
                        name=body.get("name", ""), volume_id=body.get("volume_id", ""),
                        unzip_keep_structure=common.get("unzip_keep_structure"),
                        file_storage_mode=common.get("file_storage_mode", ""),
                    )
                    self.configure_response(case, denied)
                    connector = self.client.workspace("workspace-1").connector(body["source_connector_id"])
                    if denied:
                        with self.assertRaises(sdk.Error) as failure:
                            connector.create_file_import_task(spec)
                        self.assert_owner_denial(failure.exception)
                    else:
                        handle, result = connector.create_file_import_task(spec)
                        self.assertEqual((handle.id, result.task_id), (case["response"]["task_id"],) * 2)
                    self.assertEqual(self.requests, [("POST", "/newmoi/task", "workspace-1", body)])

    def test_export_required_fields_and_owner_errors(self):
        for case in self.fixture["exports"]:
            for denied in (False, True):
                with self.subTest(case=case["name"], denied=denied):
                    self.requests.clear()
                    body = case["request"]
                    spec = sdk.ExportTaskSpec(
                        body["task_name"], body["connector_name"], body["type"],
                        sdk.ExportTaskConfig(**body["config"]),
                        [sdk.ExportTaskFile(**file) for file in body["files"]],
                        **({"creator": body["creator"]} if "creator" in body else {}),
                    )
                    self.configure_response(case, denied)
                    connector = self.client.workspace("workspace-1").connector(body["connector_id"])
                    if case.get("local_error"):
                        with self.assertRaises(sdk.Error) as failure:
                            connector.create_export_task_from_spec(spec)
                        self.assertEqual(failure.exception.code, case["local_error"])
                        self.assertEqual(self.requests, [])
                    elif denied:
                        with self.assertRaises(sdk.Error) as failure:
                            connector.create_export_task_from_spec(spec)
                        self.assert_owner_denial(failure.exception)
                        self.assertEqual(self.requests, [("POST", "/newmoi/export/task/create", "workspace-1", body)])
                    else:
                        handle, result = connector.create_export_task_from_spec(spec)
                        self.assertEqual((handle.id, result.id), (case["response"]["id"],) * 2)
                        self.assertEqual(result.name, case["response"]["name"])
                        self.assertEqual(self.requests, [("POST", "/newmoi/export/task/create", "workspace-1", body)])

    def test_explicit_import_task_id_is_preserved(self):
        case = self.fixture["explicit_task_import"]
        body = case["request"]
        for entry in ("service", "file facade"):
            with self.subTest(entry=entry):
                self.requests.clear()
                self.configure_response(case, False)
                if entry == "service":
                    spec = sdk.ImportTaskCreateSpec(body["source_connector_id"], body["config_type"], body["source_config"], task_id=body["task_id"])
                    result = self.client.connectors("workspace-1").create_task(spec)
                else:
                    common = body["source_config"]["common_file_task_config"]
                    spec = sdk.FileImportTaskSpec(body["config_type"], common["uris"], common["load_mode_config"], common["file_filter_config"], task_id=body["task_id"])
                    handle, result = self.client.workspace("workspace-1").connector(body["source_connector_id"]).create_file_import_task(spec)
                    self.assertEqual(handle.id, body["task_id"])
                self.assertEqual(result.task_id, body["task_id"])
                self.assertEqual(self.requests, [("POST", "/newmoi/task", "workspace-1", body)])

    def configure_response(self, case, denied):
        denial = self.fixture["owner_denial"]
        self.status = denial["status"] if denied else 200
        self.response = denial["body"] if denied else {"code": "OK", "data": case.get("response", {})}

    def test_import_update_requires_supported_changes(self):
        self.response = {"code": "OK", "data": None}
        service = self.client.connectors("workspace-1")
        for spec in (None, sdk.ImportTaskUpdateSpec()):
            with self.subTest(spec=spec):
                self.requests.clear()
                with self.assertRaises(sdk.Error) as failure:
                    service.update_task("task-1", spec)
                self.assertEqual(failure.exception.code, "ErrSourceConfigRequired")
                self.assertEqual(self.requests, [])
        spec = sdk.ImportTaskUpdateSpec({"load_interval_type": 7, "interval": 30}, name="renamed", file_filter_config={"file_types": [7]}, uris=["s3://bucket/资料.pdf"])
        service.update_task("task-1", spec)
        self.assertEqual(self.requests, [("POST", "/newmoi/task/update", "workspace-1", {
            "task_id": "task-1", "name": "renamed", "load_mode_config": {"load_interval_type": 7, "interval": 30},
            "file_filter_config": {"file_types": [7]}, "uris": ["s3://bucket/资料.pdf"],
        })])

    def assert_owner_denial(self, error):
        denial = self.fixture["owner_denial"]
        self.assertEqual((error.code, error.message, error.status), (denial["body"]["code"], denial["body"]["msg"], denial["status"]))


if __name__ == "__main__":
    unittest.main()
