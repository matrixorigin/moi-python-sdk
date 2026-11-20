import base64
from email.parser import BytesParser
from email.policy import default
import json
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


def read_multipart(content_type, raw):
    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw
    )
    result = {"fields": {}, "file": None}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        content = part.get_payload(decode=True)
        if name == "file":
            result["file"] = {
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        else:
            result["fields"][name] = content.decode("utf-8")
    return result


class CatalogUploadHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "catalog_upload_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                observed.update(
                    method=self.command,
                    path=self.path,
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                    multipart=read_multipart(self.headers["Content-Type"], raw),
                )
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.catalog("workspace-1")
        input_value = scenario["input"]
        options = {}
        for name in ("content_type", "external_source_uri"):
            if name in input_value:
                options[name] = input_value[name]
        content = base64.b64decode(input_value["content_base64"])
        result = None
        operation = scenario.get("operation", "upload")
        upload = service.upload_private if operation == "upload-private" else service.upload
        if scenario["status"] >= 400:
            with self.assertRaises(sdk.Error) as caught:
                upload(input_value["filename"], content, **options)
            error = caught.exception
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            result = upload(input_value["filename"], content, **options)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        self.assertEqual(observed["multipart"], scenario["multipart"])
        if result is not None:
            expected = json_format.ParseDict(scenario["response"]["data"], sdk.UploadFileResult())
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
