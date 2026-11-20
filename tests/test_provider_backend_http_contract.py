import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


RESULT_TYPES = {
    "list": sdk.ProviderBackendListResult,
    "list-models": sdk.ProviderModelListResult,
    "list-embedding-models": sdk.ProviderModelListResult,
    "create": sdk.ProviderBackend,
    "get": sdk.ProviderBackend,
    "update": sdk.ProviderBackend,
    "delete": sdk.ProviderMutationResult,
    "list-endpoints": sdk.ProviderEndpointListResult,
    "create-endpoint": sdk.ProviderEndpoint,
    "set-endpoint-status": sdk.ProviderMutationResult,
    "probe-backend-models": sdk.ProviderProbeModelsResult,
    "probe-llm-models": sdk.ProviderProbeModelsResult,
    "probe-embedding-models": sdk.ProviderProbeModelsResult,
    "router": sdk.ProviderRouterConfig,
    "update-router": sdk.ProviderRouterConfig,
    "setup-llm-backend": sdk.ProviderSetupBackendResult,
}

PARSER_ARRAY_FIELD = {"list": "backends", "list-endpoints": "endpoints"}


def backend_handle(client, kind):
    models = client.models("workspace-1")
    if kind == "embedding":
        return models.embedding_backends()
    if kind == "parser":
        return models.parser_backends()
    return models.llm_backends()


def create_options(value):
    options = []
    if "type" in value:
        options.append(sdk.with_provider_backend_type(value["type"]))
    if "reasoning_control_protocol" in value:
        options.append(sdk.with_provider_backend_reasoning_control_protocol(value["reasoning_control_protocol"]))
    if "api_key" in value:
        options.append(sdk.with_provider_backend_api_key(value["api_key"]))
    if "address" in value:
        options.append(sdk.with_provider_backend_address(value["address"]))
    if "timeout_seconds" in value:
        options.append(sdk.with_provider_backend_timeout_seconds(value["timeout_seconds"]))
    if "models" in value:
        options.append(sdk.with_provider_backend_models(*value["models"]))
    if "supported_mime_types" in value:
        options.append(sdk.with_provider_backend_supported_mime_types(*value["supported_mime_types"]))
    return options


def update_options(value):
    options = []
    if "name" in value:
        options.append(sdk.with_provider_backend_update_name(value["name"]))
    if "api_key" in value:
        options.append(sdk.with_provider_backend_update_api_key(value["api_key"]))
    if "reasoning_control_protocol" in value:
        options.append(sdk.with_provider_backend_update_reasoning_control_protocol(value["reasoning_control_protocol"]))
    if "timeout_seconds" in value:
        options.append(sdk.with_provider_backend_update_timeout_seconds(value["timeout_seconds"]))
    if "models" in value:
        options.append(sdk.with_provider_backend_update_models(*value["models"]))
    if "supported_mime_types" in value:
        options.append(sdk.with_provider_backend_update_supported_mime_types(*value["supported_mime_types"]))
    return options


def router_options(value):
    options = []
    if "strategy" in value:
        options.append(sdk.with_router_strategy(value["strategy"]))
    if "health_check_interval" in value:
        options.append(sdk.with_router_health_check_interval(value["health_check_interval"]))
    if "max_retries" in value:
        options.append(sdk.with_router_max_retries(value["max_retries"]))
    if "session_affinity" in value:
        options.append(sdk.with_router_session_affinity(value["session_affinity"]))
    return options


def query_options(scenario):
    return [
        sdk.with_query_param(key, value)
        for key, values in scenario["query"].items()
        for value in values
    ]


def call_typed(client, scenario):
    value = scenario.get("input") or {}
    models = client.models("workspace-1")
    backends = backend_handle(client, scenario["kind"])
    operation = scenario["operation"]
    if operation == "list":
        return models.list(*query_options(scenario)) if scenario["service"] == "model" else backends.list()
    if operation == "list-models":
        return models.list(*query_options(scenario))
    if operation == "list-embedding-models":
        return models.list_embedding_models()
    if operation == "create":
        return backends.create(value["name"], *create_options(value))
    if operation == "get":
        return backends.get(scenario["backend_id"])
    if operation == "update":
        return backends.update(scenario["backend_id"], *update_options(value))
    if operation == "delete":
        return backends.delete(scenario["backend_id"])
    if operation == "list-endpoints":
        return backends.list_endpoints(scenario["backend_id"])
    if operation == "create-endpoint":
        return backends.create_endpoint(scenario["backend_id"], value["address"])
    if operation == "set-endpoint-status":
        return backends.set_endpoint_status(scenario["backend_id"], scenario["endpoint_id"], value["status"])
    if operation == "probe-backend-models":
        return backends.probe_backend_models(scenario["backend_id"], *create_options(value))
    if operation == "probe-llm-models":
        return models.probe_llm_models(value["address"], *create_options(value))
    if operation == "probe-embedding-models":
        return models.probe_embedding_models(value["address"], *create_options(value))
    if operation == "router":
        return backends.router()
    if operation == "update-router":
        return backends.update_router(*router_options(value))
    if operation == "setup-llm-backend":
        return models.setup_llm_backend(value["name"], value["address"], value["models"], *create_options(value))
    raise AssertionError(f"unknown operation {operation}")


class ProviderBackendHTTPContractTest(unittest.TestCase):
    def test_provider_backend_contracts(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "provider_backend_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 37)
        current = {}
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def receive(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                target = urlsplit(self.path)
                observed.clear()
                observed.update({
                    "method": self.command,
                    "path": target.path,
                    "query": parse_qs(target.query, keep_blank_values=True),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "body": json.loads(body) if body else None,
                })
                if current.get("error_mode"):
                    status = current["error_response"]["status"]
                    payload = current["error_response"]["response"]
                else:
                    status = current["status"]
                    payload = current["response"]
                encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            do_GET = receive
            do_POST = receive
            do_PUT = receive
            do_DELETE = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)

        for scenario in cases:
            with self.subTest(case=scenario["name"]):
                current.clear()
                current.update(scenario)
                current["error_mode"] = False
                client = sdk.Client(
                    f"http://127.0.0.1:{server.server_port}/newmoi",
                    sdk.with_api_key("synthetic-key"),
                )
                result = call_typed(client, scenario)

                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertEqual(observed["api_key"], "synthetic-key")
                self.assertEqual(observed["body"], scenario["request"])

                operation = scenario["operation"]
                if scenario["kind"] == "parser" and operation in PARSER_ARRAY_FIELD:
                    field = PARSER_ARRAY_FIELD[operation]
                    item_type = sdk.ProviderBackend() if field == "backends" else sdk.ProviderEndpoint()
                    self.assertIsInstance(scenario["response"]["data"], list)
                    expected = [json_format.ParseDict(item, type(item_type)()) for item in scenario["response"]["data"]]
                    self.assertEqual(scenario["result"][field], scenario["response"]["data"])
                    self.assertEqual(list(getattr(result, field)), expected)
                else:
                    expected_raw = scenario.get("result")
                    if expected_raw is None:
                        expected_raw = scenario["response"]["data"]
                    expected = json_format.ParseDict(expected_raw, RESULT_TYPES[operation]())
                    self.assertEqual(result, expected)

                current["error_mode"] = True
                with self.assertRaises(sdk.Error) as raised:
                    call_typed(client, scenario)
                self.assertEqual(raised.exception.code, scenario["error_response"]["response"]["code"])
                self.assertEqual(raised.exception.status, scenario["error_response"]["status"])
                self.assertEqual(raised.exception.message, scenario["error_response"]["response"]["msg"])
                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertEqual(observed["api_key"], "synthetic-key")
                self.assertEqual(observed["body"], scenario["request"])


if __name__ == "__main__":
    unittest.main()
