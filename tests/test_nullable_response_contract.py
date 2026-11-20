import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


class NullableResponseContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_public_sdk_distinguishes_null_missing_and_business_errors(self):
        response = {"status": 200, "body": b""}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(response["status"])
                self.send_header("X-Request-ID", "null-contract")
                self.end_headers()
                self.wfile.write(response["body"])

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.do_GET()

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}", sdk.with_api_key("user-key"))
            calls = (
                ("query_detail", lambda: client.sql("workspace").query_detail("statement"), lambda value: value is None),
                ("parser_backends", lambda: client.models("workspace").parser_backends().list(), lambda value: len(value.backends) == 0),
                ("parser_endpoints", lambda: client.models("workspace").parser_backends().list_endpoints("backend"), lambda value: len(value.endpoints) == 0),
                ("current_credit_requires_object", lambda: client.account().current_credit(), lambda value: False),
            )
            for name, status, body, code in (
                ("null", 200, b'{"code":"OK","msg":"OK","data":null}', None),
                ("missing", 200, b'{"code":"OK","msg":"OK"}', "ErrResponseInvalid"),
                ("empty_body", 200, b"", "ErrResponseInvalid"),
                ("error_null", 409, b'{"code":"ErrConflict","msg":"conflict","data":null}', "ErrConflict"),
                ("error_missing", 409, b'{"code":"ErrConflict","msg":"conflict"}', "ErrConflict"),
                ("business_error_200", 200, b'{"code":"ErrConflict","msg":"conflict","data":null}', "ErrConflict"),
            ):
                response.update(status=status, body=body)
                for method, call, is_empty in calls:
                    with self.subTest(response=name, method=method):
                        expected_code = "ErrResponseInvalid" if name == "null" and method == "current_credit_requires_object" else code
                        if expected_code is None:
                            self.assertTrue(is_empty(call()))
                        else:
                            with self.assertRaises(sdk.Error) as raised:
                                call()
                            self.assertEqual(expected_code, raised.exception.code)
                            self.assertEqual("null-contract", raised.exception.request_id)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
