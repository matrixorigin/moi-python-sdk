import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class DataShareHTTPContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_shared_http_contracts(self):
        cases = json.loads(Path("../go-sdk/testdata/data_share_http_contract.json").read_text())
        for scenario in cases:
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    api_key=self.headers.get("X-API-Key"),
                    workspace=self.headers.get("X-Workspace-ID"),
                    body=json.loads(raw) if raw else None,
                )
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if scenario["response"] is not None:
                    self.wfile.write(json.dumps(scenario["response"]).encode())

            do_GET = _handle
            do_POST = _handle
            do_PUT = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
        service = client.data_share("workspace-1")
        input_value = scenario.get("input", {})
        query = tuple(sdk.with_query_param(key, value) for key, value in sorted(scenario.get("query", {}).items()))
        operation = scenario["operation"]
        result = None

        def scope():
            return json_format.ParseDict(input_value["table_scope"], sdk.DataShareScope())

        try:
            if operation == "publishes":
                result = service.publishes(*query)
            elif operation == "workspace-names":
                result = service.workspace_names(input_value["ids"])
            elif operation == "resolve-workspace-names":
                result = service.resolve_workspace_names(input_value["ids"])
            elif operation == "publish-summary":
                result = service.publish_summary()
            elif operation == "source-tables":
                result = service.source_tables(input_value["source_database_id"], *query)
            elif operation == "check-publish-name":
                result = service.check_publish_name(*query)
            elif operation == "create-publish":
                options = ()
                if input_value.get("remark_present"):
                    options = (sdk.with_data_share_remark(input_value.get("remark", "")),)
                result = service.create_publish(
                    input_value["name"],
                    input_value["source_database_id"],
                    scope(),
                    input_value["target_workspace_ids"],
                    *options,
                )
            elif operation == "update-publish":
                options = []
                if input_value.get("table_scope_present"):
                    options.append(sdk.with_data_share_update_table_scope(scope()))
                if input_value.get("target_workspace_ids_present"):
                    options.append(sdk.with_data_share_update_target_workspace_ids(*input_value["target_workspace_ids"]))
                if input_value.get("remark_present"):
                    options.append(sdk.with_data_share_update_remark(input_value.get("remark", "")))
                result = service.update_publish(input_value["publish_id"], *options)
            elif operation == "delete-publish":
                result = service.delete_publish(input_value["publish_id"])
            elif operation == "subscriptions":
                result = service.subscriptions(*query)
            elif operation == "subscribe":
                result = service.subscribe(input_value["subscription_id"], input_value["sub_name"])
            elif operation == "unsubscribe":
                result = service.unsubscribe(input_value["subscription_id"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
        else:
            self.assertLess(scenario["status"], 400)
            self._assert_result(scenario, result)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], {key: [value] for key, value in scenario.get("query", {}).items()})
        self.assertEqual(observed["api_key"], "user-key")
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["body"], scenario["request"])

    def _assert_result(self, scenario, result):
        operation = scenario["operation"]
        if operation in ("delete-publish", "unsubscribe"):
            self.assertIsNone(result)
            return
        message_types = {
            "publishes": sdk.DataSharePublishListResult,
            "workspace-names": sdk.DataShareWorkspaceNameListResult,
            "resolve-workspace-names": sdk.DataShareWorkspaceNameListResult,
            "publish-summary": sdk.PublishSummaryResult,
            "source-tables": sdk.DataShareSourceTableListResult,
            "check-publish-name": sdk.CheckNameResult,
            "create-publish": sdk.DataSharePublish,
            "update-publish": sdk.DataSharePublish,
            "subscriptions": sdk.DataShareSubscriptionListResult,
            "subscribe": sdk.DataShareSubscription,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], message_types[operation]())
        self.assertEqual(result, expected)
        if operation == "publish-summary":
            self.assertEqual(result.total, 9007199254740993)


if __name__ == "__main__":
    unittest.main()
