import json
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class AgentPluginHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk/testdata/agent_plugin_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observations = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                parsed = urllib.parse.urlsplit(self.path)
                observations.append({
                    "method": self.command,
                    "path": parsed.path,
                    "query": urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    "body": self.rfile.read(int(self.headers.get("Content-Length", "0"))),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "authorization": self.headers.get("Authorization"),
                    "cookie": self.headers.get("Cookie"),
                    "runtime_authorization": self.headers.get("X-MOI-Runtime-Authorization"),
                })
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
            if operation == "search-plugins":
                result = service.search_plugins(*options)
            elif operation == "describe-plugin-capability":
                result = service.describe_plugin_capability(scenario["query"]["ref"][0])
            elif operation == "list-plugin-releases":
                result = service.list_plugin_releases(*options)
            elif operation == "get-plugin-release":
                result = service.get_plugin_release(scenario["release_id"], *options)
            elif operation == "install-plugin":
                result = service.install_plugin(self._request(operation, data))
            elif operation == "list-plugin-installations":
                result = service.list_plugin_installations(*options)
            elif operation == "get-plugin-installation":
                result = service.get_plugin_installation(scenario["installation_id"])
            elif operation == "update-plugin-installation":
                result = service.update_plugin_installation(scenario["installation_id"], self._request(operation, data))
            elif operation == "delete-plugin-installation":
                result = service.delete_plugin_installation(scenario["installation_id"], data["expected_version"])
            elif operation == "create-plugin-connection":
                result = service.create_plugin_connection(self._request(operation, data))
            elif operation == "list-plugin-connections":
                result = service.list_plugin_connections(*options)
            elif operation == "get-plugin-connection":
                result = service.get_plugin_connection(scenario["connection_id"])
            elif operation == "update-plugin-connection":
                result = service.update_plugin_connection(scenario["connection_id"], self._request(operation, data))
            elif operation == "delete-plugin-connection":
                result = service.delete_plugin_connection(scenario["connection_id"], data["expected_version"])
            elif operation == "get-plugin-authorization":
                result = service.get_plugin_authorization(scenario["connection_id"])
            elif operation == "store-plugin-secret":
                result = service.store_plugin_secret(scenario["connection_id"], self._request(operation, data))
            elif operation == "begin-plugin-oauth":
                result = service.begin_plugin_oauth(scenario["connection_id"], data["expected_version"])
            elif operation == "poll-plugin-oauth":
                result = service.poll_plugin_oauth(scenario["connection_id"], scenario["attempt_id"], data["expected_version"])
            elif operation == "disconnect-plugin-connection":
                result = service.disconnect_plugin_connection(scenario["connection_id"], data["expected_generation"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            response = scenario["response"]
            self.assertEqual(error.code, str(response["code"]))
            self.assertEqual(error.message, response.get("msg", response.get("message")))
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
            self.assertEqual(error.details, response.get("details", {}))
        else:
            self.assertLess(scenario["status"], 400)
            self.assertEqual(result, self._expected_message(operation, scenario["response"]["data"]))

        self.assertEqual(len(observations), 1)
        observed = observations[0]
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
    def _request(operation, data):
        request_type = {
            "install-plugin": sdk.PluginInstallRequest,
            "update-plugin-installation": sdk.PluginUpdateInstallationRequest,
            "create-plugin-connection": sdk.PluginCreateConnectionRequest,
            "update-plugin-connection": sdk.PluginUpdateConnectionRequest,
            "store-plugin-secret": sdk.PluginStoreSecretRequest,
        }[operation]
        return json_format.ParseDict(data, request_type())

    @staticmethod
    def _expected_message(operation, data):
        message_type = {
            "search-plugins": sdk.PluginDiscoveryPage,
            "describe-plugin-capability": sdk.PluginCapabilityDescriptor,
            "list-plugin-releases": sdk.PluginPublicationList,
            "get-plugin-release": sdk.PluginRelease,
            "install-plugin": sdk.PluginInstallation,
            "list-plugin-installations": sdk.PluginInstallationList,
            "get-plugin-installation": sdk.PluginInstallation,
            "update-plugin-installation": sdk.PluginInstallation,
            "delete-plugin-installation": sdk.PluginMutationResult,
            "create-plugin-connection": sdk.PluginConnection,
            "list-plugin-connections": sdk.PluginConnectionList,
            "get-plugin-connection": sdk.PluginConnection,
            "update-plugin-connection": sdk.PluginConnection,
            "delete-plugin-connection": sdk.PluginMutationResult,
            "get-plugin-authorization": sdk.PluginAuthorizationStatus,
            "store-plugin-secret": sdk.PluginAuthorizationStatus,
            "begin-plugin-oauth": sdk.PluginOAuthAction,
            "poll-plugin-oauth": sdk.PluginOAuthProgress,
            "disconnect-plugin-connection": sdk.PluginMutationResult,
        }[operation]
        return json_format.ParseDict(data, message_type())


if __name__ == "__main__":
    unittest.main()
