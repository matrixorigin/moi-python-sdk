import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentIngressHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_ingress_http_contract.json"
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
        target = sdk.AgentTargetRef(**scenario["target"]) if "target" in scenario else None
        try:
            if operation == "list-ingress-capabilities":
                result = service.list_ingress_capabilities()
            elif operation == "list-ingress-connections":
                result = service.list_ingress_connections(target)
            elif operation == "create-ingress-connection":
                result = service.create_ingress_connection(self._create(data))
            elif operation == "resolve-we-com-qr-binding":
                result = service.resolve_we_com_qr_binding(target, data["session_token"])
            elif operation == "delete-ingress-connection":
                result = service.delete_ingress_connection(
                    scenario["connection_id"],
                    int(scenario["query"]["expected_association_version"][0]),
                    int(scenario["query"]["expected_config_version"][0]),
                )
            elif operation == "get-ingress-connection":
                result = service.get_ingress_connection(scenario["connection_id"])
            elif operation == "update-ingress-connection":
                result = service.update_ingress_connection(scenario["connection_id"], self._update(data))
            elif operation == "verify-ingress-connection":
                result = service.verify_ingress_connection(scenario["connection_id"], sdk.IngressConnectionVerifyRequest(**data))
            elif operation == "generate-we-com-callback-secrets":
                result = service.generate_we_com_callback_secrets()
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
            if operation == "generate-we-com-callback-secrets":
                self.assertEqual(result, expected)
            elif operation == "verify-ingress-connection":
                self.assertEqual(result.raw, expected)
                if "ok" in expected:
                    self.assertIsNone(result.connection)
                    self.assertEqual(result.test_result.raw, expected)
                    self.assertFalse(result.test_result.ok)
                    self.assertIsNone(result.test_result.instance)
                else:
                    self.assertIsNone(result.test_result)
                    self.assertEqual(result.connection, json_format.ParseDict(expected, sdk.IngressConnection()))
            else:
                self.assertEqual(result, self._expected_message(operation, expected))

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertIsNone(observed["runtime_authorization"])
        if "input" in scenario:
            self.assertEqual(json.loads(observed["body"]), data)
        else:
            self.assertEqual(observed["body"], b"")

    @staticmethod
    def _create(data):
        values = dict(data)
        values["target"] = sdk.AgentTargetRef(**values["target"])
        for key, request_type in (("callback", sdk.IngressCallbackConfig), ("mail_polling", sdk.IngressMailPollingConfig), ("managed_stream", sdk.IngressManagedStreamConfig)):
            if key in values:
                values[key] = request_type(**values[key])
        return sdk.IngressConnectionCreateRequest(**values)

    @staticmethod
    def _update(data):
        values = dict(data)
        managed = values.pop("managed_stream", {})
        for key, value in managed.items():
            values["managed_stream_" + key] = value
        return sdk.IngressConnectionUpdateRequest(**values)

    @staticmethod
    def _expected_message(operation, data):
        message_type = {
            "list-ingress-capabilities": sdk.IngressCapabilityList,
            "list-ingress-connections": sdk.IngressConnectionList,
            "resolve-we-com-qr-binding": sdk.WeComQRBindingResult,
            "create-ingress-connection": sdk.IngressConnection,
            "delete-ingress-connection": sdk.IngressConnection,
            "get-ingress-connection": sdk.IngressConnection,
            "update-ingress-connection": sdk.IngressConnection,
        }[operation]
        return json_format.ParseDict(data, message_type())


if __name__ == "__main__":
    unittest.main()
