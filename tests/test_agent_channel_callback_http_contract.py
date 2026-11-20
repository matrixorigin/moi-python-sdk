import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentChannelCallbackHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_channel_callback_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                parsed = urllib.parse.urlsplit(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=self.rfile.read(int(self.headers.get("Content-Length", "0"))),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    runtime_authorization=self.headers.get("X-MOI-Runtime-Authorization"),
                )
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                self.send_header("Content-Type", "application/json")
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle
            do_PATCH = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.agents("workspace-1")
        operation = scenario["operation"]
        data = scenario.get("input", {})
        options = tuple(sdk.with_query_values(key, *values) for key, values in scenario.get("query", {}).items())
        try:
            if operation == "create-channel-instance":
                result = service.create_channel_instance(scenario["provider"], self._channel_create(data))
            elif operation == "list-channel-instances":
                result = service.list_channel_instances(scenario["provider"], *options)
            elif operation == "get-channel-instance":
                result = service.get_channel_instance(scenario["provider"], scenario["instance_id"])
            elif operation == "update-channel-instance":
                result = service.update_channel_instance(scenario["provider"], scenario["instance_id"], self._channel_update(data))
            elif operation == "test-channel-configuration":
                result = service.test_channel_configuration(scenario["provider"], self._channel_create(data))
            elif operation == "disable-channel-instance":
                result = service.disable_channel_instance(scenario["provider"], scenario["instance_id"])
            elif operation == "test-channel-instance":
                result = service.test_channel_instance(scenario["provider"], scenario["instance_id"])
            elif operation == "create-callback-rule":
                result = service.create_callback_rule(self._callback_create(data))
            elif operation == "list-callback-rules":
                result = service.list_callback_rules(*options)
            elif operation == "get-callback-rule":
                result = service.get_callback_rule(scenario["rule_id"])
            elif operation == "update-callback-rule":
                result = service.update_callback_rule(scenario["rule_id"], self._callback_update(data))
            elif operation == "delete-callback-rule":
                result = service.delete_callback_rule(scenario["rule_id"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            response = scenario["response"]
            self.assertEqual(error.code, str(response["code"]))
            self.assertEqual(error.message, response.get("message", response.get("msg")))
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            expected = scenario["response"]["data"]
            self.assertEqual(result.raw, expected)
            if operation == "test-channel-configuration":
                self.assertIsNone(result.instance)
            if operation == "test-channel-instance":
                self.assertEqual(result.instance.raw, expected["instance"])
            if operation in {"create-callback-rule", "get-callback-rule", "update-callback-rule"}:
                self.assertEqual(result.match.resource_kinds, expected["match"]["resource_kinds"])
            if operation in {"create-channel-instance", "get-channel-instance", "update-channel-instance"}:
                self.assertEqual(result.labels, expected.get("labels", {}))
            if operation == "get-channel-instance":
                self.assertEqual(result.last_test_error_code, expected["last_test_error_code"])

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertIsNone(observed["runtime_authorization"])
        if "input" in scenario:
            self.assertEqual(json.loads(observed["body"]), scenario["input"])
        else:
            self.assertEqual(observed["body"], b"")

    @staticmethod
    def _match(data):
        return sdk.CallbackRuleMatch(**data)

    @classmethod
    def _channel_create(cls, data):
        return sdk.ChannelInstanceCreateRequest(data["channel_type"], **{key: value for key, value in data.items() if key != "channel_type"})

    @staticmethod
    def _channel_update(data):
        return sdk.ChannelInstanceUpdateRequest(**data)

    @classmethod
    def _callback_create(cls, data):
        values = dict(data)
        if "match" in values:
            values["match"] = cls._match(values["match"])
        return sdk.CallbackRuleCreateRequest(**values)

    @classmethod
    def _callback_update(cls, data):
        values = dict(data)
        if "match" in values:
            values["match"] = cls._match(values["match"])
        return sdk.CallbackRuleUpdateRequest(**values)


if __name__ == "__main__":
    unittest.main()
