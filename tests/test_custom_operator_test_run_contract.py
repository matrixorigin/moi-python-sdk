import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


def _serve_payload(payload):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"code": "OK", "data": payload}).encode())

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _envelope(developer_logs):
    return {
        "test_run": {
            "operator_id": "220001",
            "node_id": "220001",
            "version": "1",
            "task_id": "01a18e9c-6d00-7000-8000-000000000000",
            "case_id": "01a18e9c-701d-7147-8598-5957c9caeb9a",
            "status": "failed",
            "case_result": "",
            "case_error": "handler failed: nsjail sandbox execution failed: returncode=7",
            "developer_logs": developer_logs,
        }
    }


class CustomOperatorTestRunContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def _run_test(self, payload):
        server, thread = _serve_payload(payload)
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("user-key"))
            return client.workspace("ws-1").custom_operator("220001").test({"action": "exit7"})
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_decodes_termination_diagnostics_in_failed_run(self):
        # Regression for matrixflow#13107: worker now reports sandbox termination
        # diagnostics; strict decoding must not reject the response.
        result = self._run_test(_envelope({
            "stdout": "",
            "stderr": "close_range(CLOSE_RANGE_CLOEXEC): Invalid argument",
            "stream": "close_range(CLOSE_RANGE_CLOEXEC): Invalid argument",
            "stdout_bytes": 0,
            "stderr_bytes": 47,
            "stream_bytes": 47,
            "runner": "nsjail",
            "output_limited": False,
            "returncode": 7,
            "signal": "",
            "elapsed_seconds": 0.2182131150038913,
        }))
        logs = result.test_run.developer_logs
        self.assertEqual(7, logs.returncode)
        self.assertEqual("", logs.signal)
        self.assertAlmostEqual(0.2182131150038913, logs.elapsed_seconds)
        self.assertEqual("nsjail", logs.runner)
        self.assertIn("close_range", logs.stderr)

    def test_decodes_negative_returncode_and_signal(self):
        # SIGKILL termination surfaces returncode=-9 with the resolved signal name.
        result = self._run_test(_envelope({
            "stdout": "",
            "stderr": "close_range(CLOSE_RANGE_CLOEXEC): Invalid argument",
            "stream": "",
            "stdout_bytes": 0,
            "stderr_bytes": 47,
            "stream_bytes": 0,
            "runner": "nsjail",
            "output_limited": False,
            "returncode": -9,
            "signal": "SIGKILL",
            "elapsed_seconds": 0.102,
        }))
        logs = result.test_run.developer_logs
        self.assertEqual(-9, logs.returncode)
        self.assertEqual("SIGKILL", logs.signal)

    def test_decodes_legacy_response_without_diagnostics(self):
        # Workers predating the diagnostics fields omit them; decoding must keep working.
        result = self._run_test(_envelope({
            "stdout": "",
            "stderr": "ordinary failure",
            "stream": "ordinary failure",
            "stdout_bytes": 0,
            "stderr_bytes": 16,
            "stream_bytes": 16,
            "runner": "nsjail",
            "output_limited": False,
        }))
        logs = result.test_run.developer_logs
        self.assertEqual(0, logs.returncode)
        self.assertEqual("", logs.signal)
        self.assertEqual(0.0, logs.elapsed_seconds)


if __name__ == "__main__":
    unittest.main()
