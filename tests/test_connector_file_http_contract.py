import base64
from email.parser import BytesParser
from email.policy import default
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


def read_connector_multipart(content_type, raw):
    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw
    )
    result = {"fields": {}, "files": []}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        content = part.get_payload(decode=True)
        if part.get_filename() is not None:
            result["files"].append({
                "field_name": name,
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            })
        else:
            result["fields"][name] = content.decode("utf-8")
    return result


class ConnectorFileHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "connector_file_http_contract.json"
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}
        content = base64.b64decode(scenario.get("content_base64", ""))

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                parsed = urllib.parse.urlparse(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    accept=self.headers.get("Accept"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
                if "multipart" in scenario:
                    observed["multipart"] = read_connector_multipart(self.headers["Content-Type"], raw)
                else:
                    observed["body"] = json.loads(raw) if raw else None
                self.send_response(scenario["status"])
                if scenario["operation"] == "file-stream":
                    payload = content
                    self.send_header("Content-Type", "application/octet-stream")
                else:
                    payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                    self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.connectors("workspace-1")
        input_value = scenario["input"]
        operation = scenario["operation"]
        result = None
        if operation == "files":
            options = [sdk.with_query_values(key, *values) for key, values in input_value["query_params"].items()]
            result = service.files(*options)
        elif operation in ("upload", "local-upload"):
            files = [
                ("file", item["filename"], base64.b64decode(item["content_base64"]))
                for item in input_value["files"]
            ]
            if operation == "upload":
                result = service.upload(files, input_value["fields"])
            else:
                result = service.local_upload(files)
        elif operation == "file-download":
            result = service.file_download(input_value["conn_file_id"])
        elif operation == "file-stream":
            stream = service.file_stream(input_value["conn_file_id"])
            try:
                result = stream.read()
            finally:
                stream.close()
        elif operation == "file-delete":
            result = service.file_delete(input_value["conn_file_id"])
        else:
            self.fail(f"unknown operation {operation}")

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        if "multipart" in scenario:
            self.assertEqual(observed["multipart"], scenario["multipart"])
        else:
            self.assertEqual(observed["body"], scenario["request"])
        if operation == "file-stream":
            self.assertEqual(observed["accept"], "*/*")
            self.assertEqual(result, content)
            return
        if operation == "file-delete":
            self.assertIsNone(result)
            return
        result_types = {
            "files": sdk.ConnectorFileListResult,
            "upload": sdk.UploadResponse,
            "local-upload": sdk.LocalUploadResult,
            "file-download": sdk.FileDownloadResult,
        }
        expected = json_format.ParseDict(scenario["response"]["data"], result_types[operation]())
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
