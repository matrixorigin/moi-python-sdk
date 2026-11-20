import json
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


SINGLE_RESULT_TYPES = {
    "admin-preflight-delete": sdk.ComputeDeletePreflightResult,
    "preflight-delete": sdk.ComputeDeletePreflightResult,
    "admin-resume": sdk.ComputeResource,
    "admin-retry": sdk.ComputeResource,
    "admin-suspend": sdk.ComputeResource,
    "resume": sdk.ComputeResource,
    "retry": sdk.ComputeResource,
    "suspend": sdk.ComputeResource,
    "spec-management-permission": sdk.ComputeResourceSpecManagementPermission,
    "set-spec-enabled": sdk.ComputeResourceSpec,
    "adopt-legacy-ownership": sdk.ComputeResourceOwnership,
}


def call_compute(service, scenario):
    operation = scenario["operation"]
    resource_id = scenario.get("input", {}).get("id", "")
    options = tuple(
        sdk.with_query_values(key, *values)
        for key, values in sorted(scenario.get("query", {}).items())
    )
    if operation == "admin-delete":
        return service.admin_delete(resource_id, *options)
    if operation == "admin-preflight-delete":
        return service.admin_preflight_delete(resource_id)
    if operation == "admin-resume":
        return service.admin_resume(resource_id)
    if operation == "admin-retry":
        return service.admin_retry(resource_id)
    if operation == "admin-runtime":
        return service.admin_runtime(resource_id)
    if operation == "admin-suspend":
        return service.admin_suspend(resource_id)
    if operation == "specs":
        return service.specs()
    if operation == "spec-management-permission":
        return service.spec_management_permission()
    if operation == "set-spec-enabled":
        return service.set_spec_enabled(resource_id, scenario["enabled"])
    if operation == "list":
        return service.list(*options)
    if operation == "py-deps-limits":
        return service.py_deps_limits()
    if operation == "worker-images":
        return service.worker_images(*options)
    if operation == "delete":
        return service.delete(resource_id, *options)
    if operation == "adopt-legacy-ownership":
        return service.adopt_legacy_ownership(resource_id)
    if operation == "preflight-delete":
        return service.preflight_delete(resource_id)
    if operation == "resume":
        return service.resume(resource_id)
    if operation == "retry":
        return service.retry(resource_id)
    if operation == "runtime":
        return service.runtime(resource_id)
    if operation == "suspend":
        return service.suspend(resource_id)
    if operation == "workers":
        return service.workers(resource_id)
    raise AssertionError(f"unknown operation {operation}")


class ComputeRemainingHTTPContractTest(unittest.TestCase):
    def assert_typed_result(self, result, scenario):
        operation = scenario["operation"]
        data = scenario["response"]["data"]
        if operation in {"admin-delete", "delete"}:
            self.assertIsNone(result)
            return
        if operation in {"admin-runtime", "runtime"}:
            expected = json_format.ParseDict(data, sdk.ComputeWorkerRuntimeListResult())
            self.assertEqual(list(result), list(expected.runtimes))
            return
        if operation == "workers":
            self.assertEqual(result, [sdk.ComputeResourceWorker(**item) for item in data])
            return
        if operation == "py-deps-limits":
            self.assertEqual(result, sdk.ComputePyDepsLimits(**data))
            return
        if operation in {"specs", "list", "worker-images"}:
            result_type = {
                "specs": sdk.ComputeResourceSpec,
                "list": sdk.ComputeResource,
                "worker-images": sdk.WorkerImage,
            }[operation]
            self.assertEqual(result, [json_format.ParseDict(item, result_type()) for item in data])
            return
        expected = json_format.ParseDict(data, SINGLE_RESULT_TYPES[operation]())
        self.assertEqual(result, expected)

    def assert_request(self, observed, scenario):
        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], "/newmoi" + scenario["path"])
        self.assertEqual(observed["query"], scenario["query"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        if scenario.get("bodyless"):
            self.assertIn(observed["body"], (None, {}))
        else:
            self.assertEqual(observed["body"], scenario["request"])

    def test_typed_compute_routes(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "compute_remaining_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 20)
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
                payload = json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = receive
            do_POST = receive
            do_PATCH = receive
            do_DELETE = receive

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)

        def serve(scenario):
            current.clear()
            current.update(scenario)
            observed.clear()
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
            return client

        for scenario in cases:
            with self.subTest(case=f"{scenario['api_id']} {scenario['name']}"):
                client = serve(scenario)
                result = call_compute(client.compute("workspace-1"), scenario)
                self.assertTrue(observed, "typed SDK did not issue a request")
                self.assert_request(observed, scenario)
                self.assert_typed_result(result, scenario)

                error_case = dict(scenario)
                error_case["status"] = scenario["error"]["status"]
                error_case["response"] = scenario["error"]["response"]
                error_client = serve(error_case)
                with self.assertRaises(sdk.Error) as raised:
                    call_compute(error_client.compute("workspace-1"), scenario)
                failure = raised.exception
                self.assertEqual(failure.code, scenario["error"]["response"]["code"])
                self.assertEqual(failure.status, scenario["error"]["status"])
                self.assertEqual(failure.message, scenario["error"]["response"]["message"])
                self.assertTrue(observed, "typed SDK error call did not issue a request")
                self.assert_request(observed, scenario)


if __name__ == "__main__":
    unittest.main()
