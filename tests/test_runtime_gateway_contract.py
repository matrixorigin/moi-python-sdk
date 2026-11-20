import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class RuntimeGatewayContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_compute_event_executor_authorization_and_health(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def record(self, status, response=None):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.path, self.headers.get("Authorization"), self.headers.get("X-API-Key"), self.headers.get("X-Workspace-ID"), json.loads(raw) if raw else None))
                self.send_response(status)
                if response is not None:
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.end_headers()

            def do_POST(self):
                if self.path == "/api/v1/internal/compute-bindings/events":
                    self.record(200, {"binding": {"compute_binding_id": "binding-1"}, "duplicate": False})
                elif self.path == "/api/v1/runtime-executors/authorize":
                    self.record(204)
                else:
                    self.record(404, {"code": "NOT_FOUND"})

            def do_GET(self):
                self.record(200, {"code": "OK", "data": {"executors": [{"id": "runner-1", "connected": True, "connected_secs": 9007199254740993, "ready": True}], "astra_reachable": True}})

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        endpoint = f"http://127.0.0.1:{server.server_port}/newmoi"
        runtime = sdk.Client(endpoint, sdk.with_token("runtime-grant"))
        event = sdk.ComputeBindingEvent(
            compute_binding_id="binding-1", event_type="activation_requested", workspace_id="workspace-1",
            subject_type="agent", subject_id="agent-1", edge_agent_id="edge-1", compute_resource_id="compute-1",
            spec_id="spec-1", placement_profile="default", units=2, lifecycle_instance_id="lifecycle-1",
            fencing_token=9007199254740993, kind="sandbox", idempotency_key="event-1", occurred_at="2026-11-10T01:02:03Z",
        )
        result = runtime.runtime_gateway().apply_compute_binding_event(event)
        self.assertFalse(result["duplicate"])
        self.assertEqual(requests[0][4], {
            "compute_binding_id": "binding-1", "event_type": "activation_requested", "workspace_id": "workspace-1",
            "subject_type": "agent", "subject_id": "agent-1", "edge_agent_id": "edge-1", "compute_resource_id": "compute-1",
            "spec_id": "spec-1", "placement_profile": "default", "units": 2, "lifecycle_instance_id": "lifecycle-1",
            "fencing_token": 9007199254740993, "kind": "sandbox", "idempotency_key": "event-1", "occurred_at": "2026-11-10T01:02:03Z",
        })
        self.assertIsInstance(requests[0][4]["fencing_token"], int)
        authorization = sdk.RuntimeExecutorAuthorizationRequest(task_id="task-1", executor_id="executor-1", run_id="run-1", turn_chain_id="turn-1", tool_call_id="tool-1")
        self.assertIsNone(runtime.runtime_gateway().authorize_executor(authorization))
        self.assertEqual(requests[1][4], {"task_id": "task-1", "executor_id": "executor-1", "run_id": "run-1", "turn_chain_id": "turn-1", "tool_call_id": "tool-1"})
        product = sdk.Client(endpoint, sdk.with_api_key("user-key"))
        health = product.agents("workspace-1").executor_health()
        self.assertEqual(health.executors[0].connected_secs, 9007199254740993)
        self.assertEqual(requests[0][1], "Bearer runtime-grant")
        self.assertEqual(requests[1][1], "Bearer runtime-grant")
        self.assertEqual(requests[2][2:], ("user-key", "workspace-1", None))


    def test_edge_model_rpc_and_stream(self):
        requests = []
        stream_bytes = b'data: {"choices":[]}\n\ndata: [DONE]\n\n'

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                requests.append((self.path, self.headers.get("Authorization"), json.loads(raw)))
                responses = {
                    "/api/v1/astra/edge-tokens/check": (200, {"code": 0, "data": {"ok": True, "subject": "subject-1", "workspace_id": "workspace-1", "edge_agent_id": "edge-1", "expires_at": "2026-11-10T02:00:00Z"}}),
                    "/newmoi/edge-tokens/renew": (200, {"code": 0, "data": {"token": "fresh-edge", "expires_at": "2026-11-10T03:00:00Z"}}),
                    "/api/v1/models/resolve": (200, {"model": "model-1", "status": "ready", "protocol": "openai", "invoke": {"url": "http://model.test/v1"}}),
                    "/api/v1/mcp/http": (200, {"jsonrpc": "2.0", "id": "rpc-1", "result": {"tools": []}}),
                }
                if self.path == "/api/v1/models/openai/chat/completions":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    self.wfile.write(stream_bytes)
                    return
                status, response = responses[self.path]
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_token("runtime-grant"))
        gateway = client.runtime_gateway()
        checked = gateway.check_edge_token("edge-registration")
        self.assertEqual((checked.ok, checked.subject, checked.workspace_id, checked.edge_agent_id), (True, "subject-1", "workspace-1", "edge-1"))
        renewed = gateway.renew_edge_token("edge-registration")
        self.assertEqual(renewed.token, "fresh-edge")
        resolved = gateway.resolve_model(sdk.RuntimeModelResolveRequest(model="model-1", gateway="control-plane"))
        self.assertEqual((resolved.model, resolved.invoke.url), ("model-1", "http://model.test/v1"))
        rpc = sdk.RuntimeRPCRequest(jsonrpc="2.0", method="tools/list")
        rpc.id.string_value = "rpc-1"
        rpc.params.update({"cursor": "next"})
        self.assertIn("tools", gateway.mcp(rpc).result.fields)
        stream = gateway.invoke_model({"model": "model-1", "messages": [{"role": "user", "content": "hello"}], "stream": True})
        self.assertEqual(stream.read(), stream_bytes)
        stream.close()
        self.assertEqual([item[0] for item in requests], [
            "/api/v1/astra/edge-tokens/check", "/newmoi/edge-tokens/renew", "/api/v1/models/resolve",
            "/api/v1/mcp/http", "/api/v1/models/openai/chat/completions",
        ])
        self.assertTrue(all(item[1] == "Bearer runtime-grant" for item in requests))
        self.assertEqual(requests[0][2], {"token": "edge-registration"})
        self.assertEqual(requests[1][2], {"token": "edge-registration"})
        self.assertEqual(requests[2][2], {"model": "model-1", "gateway": "control-plane"})
        self.assertEqual(requests[3][2], {"jsonrpc": "2.0", "id": "rpc-1", "method": "tools/list", "params": {"cursor": "next"}})
        self.assertEqual(requests[4][2], {"model": "model-1", "messages": [{"role": "user", "content": "hello"}], "stream": True})


if __name__ == "__main__":
    unittest.main()
