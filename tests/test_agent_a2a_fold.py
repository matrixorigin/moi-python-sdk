import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment

# Wire contract frozen by matrixflow#16009 T1: message/send answers with a
# persisted task (submitted/working) or an acknowledgement message; the SDK
# fold follows tasks/resubscribe (eventCursor resume) or tasks/get polling to
# the terminal set below. The mock speaks the raw JSON-RPC envelope, not the
# product code/msg/data envelope.
TERMINAL_STATES = ("completed", "failed", "canceled", "rejected", "input-required", "auth-required")


def _task(task_id, state, cursor):
    return {
        "kind": "task",
        "id": task_id,
        "contextId": "ctx-1",
        "status": {"state": state, "timestamp": "2026-11-05T00:00:00Z"},
        "artifacts": [],
        "metadata": {"eventCursor": cursor, "agentId": "agent-1"},
    }


def _status_update(task_id, state, seq, final):
    return {
        "kind": "status-update",
        "taskId": task_id,
        "contextId": "ctx-1",
        "status": {"state": state, "timestamp": "2026-11-05T00:00:00Z"},
        "final": final,
        "metadata": {"eventCursor": seq},
    }


def _sse_frame(handler, seq, value):
    payload = json.dumps({"jsonrpc": "2.0", "id": "fold-sub", "result": value}, separators=(",", ":"))
    handler.wfile.write(f"id: {seq}\nevent: message\ndata: {payload}\n\n".encode("utf-8"))
    handler.wfile.flush()


def _sse_heartbeat(handler):
    handler.wfile.write(b": heartbeat\n\n")
    handler.wfile.flush()


class _A2AHandler(BaseHTTPRequestHandler):
    config: dict = {}

    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        self.__class__.config["requests"].append(body)
        if self.path != "/newmoi/agents/a2a":
            self.send_error(404)
            return
        method = body.get("method")
        if method == "message/send":
            self._rpc_result(body, self.__class__.config["send_result"])
            return
        if method == "tasks/get":
            results = self.__class__.config["get_results"]
            index = min(self.__class__.config["get_calls"], len(results) - 1)
            self.__class__.config["get_calls"] += 1
            self._rpc_result(body, results[index])
            return
        if method == "tasks/resubscribe":
            params = body.get("params") or {}
            self.__class__.config["after_seqs"].append(params.get("afterSeq"))
            error = self.__class__.config.get("stream_error")
            if error is not None:
                status, code, message = error
                payload = json.dumps({"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": code, "message": message}}).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                self.__class__.config["stream_script"](self, params.get("afterSeq") or 0)
            except (BrokenPipeError, ConnectionResetError):
                pass  # The client deliberately closed the stream.
            return
        self.send_error(404)

    def _rpc_result(self, body, result):
        payload = json.dumps({"jsonrpc": "2.0", "id": body.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AgentA2AFoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), _A2AHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        self.enterContext(loopback_proxy_environment())
        self._reset_wire()

    def _reset_wire(self):
        _A2AHandler.config = {"requests": [], "after_seqs": [], "get_calls": 0}

    def _agent(self, *opts):
        client = sdk.Client(f"http://127.0.0.1:{self.server.server_port}/newmoi", sdk.with_api_key("test-key"), *opts)
        return client.workspace("ws-1").agent_by_code("explore")

    def _methods(self):
        return [request.get("method") for request in _A2AHandler.config["requests"]]

    def test_task_id_unwraps_json_rpc_envelope(self):
        enveloped = sdk.AgentA2AResult(json='{"jsonrpc":"2.0","id":"req-9","result":{"kind":"task","id":"task-1","turnId":"turn-1"}}')
        self.assertEqual(sdk.agent_a2a_task_id(enveloped), "task-1")
        self.assertEqual(sdk.agent_a2a_turn_id(enveloped), "turn-1")
        self.assertEqual(sdk.agent_a2a_payload(enveloped)["id"], "task-1")
        bare = sdk.AgentA2AResult(json='{"kind":"task","id":"task-2"}')
        self.assertEqual(sdk.agent_a2a_task_id(bare), "task-2")
        nested = sdk.AgentA2AResult(json='{"result":{"kind":"task","id":"task-3"}}')
        self.assertEqual(sdk.agent_a2a_task_id(nested), "task-3")
        with self.assertRaises(sdk.Error) as missing:
            sdk.agent_a2a_task_id(sdk.AgentA2AResult(json='{"jsonrpc":"2.0","id":"req-9","result":{"kind":"task"}}'))
        self.assertEqual(missing.exception.code, "ErrResponseInvalid")

    def test_send_text_folds_running_task_to_every_terminal_state(self):
        for state in TERMINAL_STATES:
            with self.subTest(state=state):
                self._reset_wire()
                _A2AHandler.config.update(
                    send_result=_task("task-1", "submitted", 1),
                    get_results=[_task("task-1", state, 3)],
                    stream_script=lambda handler, after_seq, state=state: (
                        _sse_heartbeat(handler),
                        _sse_frame(handler, 2, _status_update("task-1", "working", 2, False)),
                        _sse_frame(handler, 3, _status_update("task-1", state, 3, True)),
                    ),
                )
                result = self._agent().send_text(sdk.AgentTextMessage("show revenue", "msg-1", request_id="req-send-1"))
                payload = sdk.agent_a2a_payload(result)
                self.assertEqual(payload["id"], "task-1")
                self.assertEqual(payload["status"]["state"], state)
                self.assertEqual(self._methods(), ["message/send", "tasks/resubscribe", "tasks/get"])
                self.assertEqual(_A2AHandler.config["after_seqs"], [1])

    def test_no_wait_returns_task_admission_without_following(self):
        for state in ("submitted", "working"):
            with self.subTest(state=state):
                self._reset_wire()
                _A2AHandler.config["send_result"] = _task("task-1", state, 3)
                params = sdk.AgentTextMessage("show revenue", "msg-1").params()
                result = self._agent().a2a(sdk.A2ARequest(
                    sdk.A2A_METHOD_SEND,
                    id_="req-send-1",
                    params=params,
                    model="model-1",
                    no_wait=True,
                ))
                self.assertEqual(sdk.agent_a2a_task_id(result), "task-1")
                self.assertEqual(sdk.agent_a2a_payload(result)["status"]["state"], state)
                self.assertEqual(_A2AHandler.config["requests"], [{
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "id": "req-send-1",
                    "params": params,
                    "model": "model-1",
                    "agent_code": "explore",
                }])

    def test_send_text_wait_budget_outlives_request_timeout(self):
        # The follow is bounded by with_a2a_wait_timeout (default 600s), not by
        # the per-request timeout: heartbeats keep a longer-than-timeout wait
        # alive until the terminal frame lands.
        def script(handler, after_seq):
            _sse_frame(handler, 2, _status_update("task-1", "working", 2, False))
            for _ in range(7):
                time.sleep(0.05)
                _sse_heartbeat(handler)
            _sse_frame(handler, 3, _status_update("task-1", "completed", 3, True))

        _A2AHandler.config.update(
            send_result=_task("task-1", "submitted", 1),
            get_results=[_task("task-1", "completed", 3)],
            stream_script=script,
        )
        started = time.monotonic()
        result = self._agent(sdk.with_timeout(0.2)).send_text(sdk.AgentTextMessage("slow report", "msg-1"))
        elapsed = time.monotonic() - started
        self.assertEqual(sdk.agent_a2a_payload(result)["status"]["state"], "completed")
        self.assertGreaterEqual(elapsed, 0.35)

    def test_send_text_reconnects_after_stream_drop_from_event_cursor(self):
        def script(handler, after_seq):
            if after_seq == 1:
                _sse_frame(handler, 2, _status_update("task-1", "working", 2, False))
                return  # The connection drops before the terminal frame.
            _sse_frame(handler, 3, _status_update("task-1", "completed", 3, True))

        _A2AHandler.config.update(
            send_result=_task("task-1", "submitted", 1),
            get_results=[_task("task-1", "completed", 3)],
            stream_script=script,
        )
        result = self._agent().send_text(sdk.AgentTextMessage("show revenue", "msg-1"))
        self.assertEqual(sdk.agent_a2a_payload(result)["status"]["state"], "completed")
        # The resume continues from the last delivered durable sequence instead
        # of replaying or skipping events.
        self.assertEqual(_A2AHandler.config["after_seqs"], [1, 2])
        self.assertEqual(self._methods(), ["message/send", "tasks/resubscribe", "tasks/resubscribe", "tasks/get"])

    def test_send_text_polls_readback_when_projection_lags_terminal_frame(self):
        # The terminal stream frame can precede the persisted terminal
        # projection: the follow must poll tasks/get for the settled state
        # instead of re-opening a stream whose cursor already passed the final
        # event (which would idle on heartbeats until the wait budget dies).
        _A2AHandler.config.update(
            send_result=_task("task-1", "working", 1),
            get_results=[_task("task-1", "working", 3), _task("task-1", "completed", 3)],
            stream_script=lambda handler, after_seq: _sse_frame(handler, 3, _status_update("task-1", "completed", 3, True)),
        )
        started = time.monotonic()
        result = self._agent().send_text(sdk.AgentTextMessage("show revenue", "msg-1"))
        elapsed = time.monotonic() - started
        self.assertEqual(sdk.agent_a2a_payload(result)["status"]["state"], "completed")
        self.assertEqual(self._methods(), ["message/send", "tasks/resubscribe", "tasks/get", "tasks/get"])
        # One poll interval of lag, nowhere near the 600s default budget.
        self.assertGreaterEqual(elapsed, 1.9)
        self.assertLess(elapsed, 30)

    def test_send_text_degrades_to_polling_when_sse_unavailable(self):
        _A2AHandler.config.update(
            send_result=_task("task-1", "working", 1),
            get_results=[_task("task-1", "working", 1), _task("task-1", "completed", 3)],
            stream_error=(400, -32601, "method not supported"),
        )
        started = time.monotonic()
        result = self._agent().send_text(sdk.AgentTextMessage("show revenue", "msg-1"))
        elapsed = time.monotonic() - started
        self.assertEqual(sdk.agent_a2a_payload(result)["status"]["state"], "completed")
        self.assertEqual(self._methods(), ["message/send", "tasks/resubscribe", "tasks/get", "tasks/get"])
        # The poll interval is the contract-fixed 2s, not a hot loop.
        self.assertGreaterEqual(elapsed, 1.9)

    def test_send_text_wait_timeout_carries_task_id(self):
        _A2AHandler.config.update(
            send_result=_task("task-slow", "working", 1),
            get_results=[_task("task-slow", "working", 1)],
            stream_error=(400, -32601, "method not supported"),
        )
        started = time.monotonic()
        with self.assertRaises(sdk.Error) as raised:
            self._agent(sdk.with_a2a_wait_timeout(1.0)).send_text(sdk.AgentTextMessage("show revenue", "msg-1"))
        elapsed = time.monotonic() - started
        self.assertEqual(raised.exception.code, "ErrTimeout")
        self.assertEqual(raised.exception.details["task_id"], "task-slow")
        self.assertGreaterEqual(elapsed, 0.9)
        self.assertLess(elapsed, 10)

    def test_send_text_passes_through_acknowledgement_and_settled_task(self):
        ack = {
            "kind": "message",
            "role": "agent",
            "messageId": "msg-1",
            "contextId": "ctx-1",
            "parts": [{"kind": "data", "data": {"type": "moi.feedback.received", "status": "recorded"}}],
        }
        for name, send_result in (
            ("ack", ack),
            ("settled", _task("task-1", "completed", 3)),
            ("interrupted", _task("task-1", "input-required", 3)),
        ):
            with self.subTest(shape=name):
                self._reset_wire()
                _A2AHandler.config.update(send_result=send_result)
                result = self._agent().send_text(sdk.AgentTextMessage("feedback", "msg-1"))
                self.assertEqual(sdk.agent_a2a_payload(result)["kind"], send_result["kind"])
                self.assertEqual(self._methods(), ["message/send"])


if __name__ == "__main__":
    unittest.main()
