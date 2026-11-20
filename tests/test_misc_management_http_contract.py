import base64
import json
import pathlib
import threading
import unittest
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from google.protobuf import json_format

import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class MiscManagementHTTPContractTest(unittest.TestCase):
    def test_json_multipart_and_stream_contracts(self):
        self.enterContext(loopback_proxy_environment())
        path = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "misc_management_http_contract.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
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
                    "method": self.command, "path": target.path,
                    "query": parse_qs(target.query, keep_blank_values=True),
                    "workspace": self.headers.get("X-Workspace-ID"),
                    "api_key": self.headers.get("X-API-Key"),
                    "runtime": self.headers.get("X-MOI-Runtime-Authorization"),
                    "body": body,
                })
                operation = current["operation"]
                if operation in {"upload-workspace-file", "upload-runtime-artifact", "analyze-runtime-image"}:
                    message = BytesParser(policy=default).parsebytes(
                        b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + body
                    )
                    parts = list(message.iter_parts())
                    file_parts = [part for part in parts if part.get_param("name", header="content-disposition") == "file"]
                    self_test.assertEqual(len(file_parts), 1)
                    file_part = file_parts[0]
                    observed["filename"] = file_part.get_filename()
                    observed["file_content_type"] = file_part.get_content_type()
                    observed["content"] = file_part.get_payload(decode=True)
                    if operation == "analyze-runtime-image":
                        question = next(part for part in parts if part.get_param("name", header="content-disposition") == "question")
                        observed["question"] = question.get_payload(decode=True).decode("utf-8")
                else:
                    observed["json"] = json.loads(body) if body else None
                if current.get("response_base64"):
                    payload = base64.b64decode(current["response_base64"])
                else:
                    payload = json.dumps(current["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(current["status"])
                self.send_header("Content-Type", current.get("response_content_type") or "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = receive
            do_POST = receive

        self_test = self
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
                options = [sdk.with_api_key("synthetic-key")]
                if scenario.get("runtime_authorization"):
                    options.append(sdk.with_runtime_authorization(scenario["runtime_authorization"]))
                client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", *options)
                content = base64.b64decode(scenario.get("content_base64", ""))
                operation = scenario["operation"]
                if operation == "upload-workspace-file":
                    result = client.agents("workspace-1").upload_workspace_file(scenario["filename"], content)
                    self.assertEqual(result, scenario["response"]["data"])
                elif operation == "get-skill-file":
                    stream = client.agents("workspace-1").get_skill_file(scenario["skill_id"], scenario["file_path"])
                    try:
                        self.assertEqual(stream.read(), base64.b64decode(scenario["response_base64"]))
                    finally:
                        stream.close()
                elif operation == "list-connector-catalog":
                    result = client.agents("workspace-1").list_connector_catalog()
                    self.assertEqual(result.raw, scenario["response"]["data"])
                elif operation == "invoke-dynamic-service":
                    value = scenario["input"]
                    spec = sdk.DynamicServiceInvokeSpec(
                        value["service_name"], value["payload"], value["version_number"],
                        version=value.get("version", ""), trace=value.get("trace"),
                    )
                    result = client.workflows("workspace-1").invoke_dynamic_service(spec)
                    actual = {key: getattr(result, key) for key in ("case_id", "run_id", "status", "result", "error", "result_url") if getattr(result, key) is not None}
                    self.assertEqual(actual, scenario["response"]["data"])
                elif operation == "garbage-collection":
                    request = json_format.ParseDict(scenario["input"], sdk.CatalogGarbageCollectionRequest())
                    result = client.catalog("workspace-1").garbage_collection(request)
                    expected = json_format.ParseDict(scenario["response"]["data"], sdk.CatalogGarbageCollectionResult())
                    self.assertEqual(result, expected)
                elif operation == "upload-runtime-artifact":
                    result = client.catalog("workspace-1").upload_runtime_artifact(scenario["filename"], content)
                    expected = json_format.ParseDict(scenario["response"]["data"], sdk.RuntimeArtifactUploadResult())
                    self.assertEqual(result, expected)
                elif operation == "analyze-runtime-image":
                    result = client.catalog("workspace-1").analyze_runtime_image(scenario["filename"], content, scenario["question"])
                    expected = json_format.ParseDict(scenario["response"]["data"], sdk.RuntimeImageAnalysisResult())
                    self.assertEqual(result, expected)
                else:
                    self.fail(f"unknown operation {operation}")

                self.assertEqual(observed["method"], scenario["method"])
                self.assertEqual(observed["path"], scenario["path"])
                self.assertEqual(observed["query"], scenario["query"])
                self.assertEqual(observed["workspace"], "workspace-1")
                self.assertEqual(observed["api_key"], "synthetic-key")
                self.assertEqual(observed["runtime"], scenario.get("runtime_authorization"))
                if operation in {"upload-workspace-file", "upload-runtime-artifact", "analyze-runtime-image"}:
                    self.assertEqual(observed["filename"], scenario["filename"])
                    self.assertEqual(observed["file_content_type"], scenario["content_type"])
                    self.assertEqual(observed["content"], content)
                    if operation == "analyze-runtime-image":
                        self.assertEqual(observed["question"], scenario["question"])
                else:
                    self.assertEqual(observed["json"], scenario["request"])


if __name__ == "__main__":
    unittest.main()
