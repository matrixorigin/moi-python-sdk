import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk


_LOCALHOST_NO_PROXY = ("127.0.0.1", "localhost", "::1")


def _with_localhost_no_proxy(value):
    entries = []
    seen = set()
    for item in (value or "").split(","):
        item = item.strip()
        if item and item not in seen:
            entries.append(item)
            seen.add(item)
    for item in _LOCALHOST_NO_PROXY:
        if item not in seen:
            entries.append(item)
    return ",".join(entries)


class _RuntimeArtifactHandler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, format, *args):
        return

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.__class__.requests.append(
            {
                "method": "POST",
                "path": self.path,
                "workspace_id": self.headers.get("X-Workspace-ID"),
                "runtime_authorization": self.headers.get("X-MOI-Runtime-Authorization"),
                "content_type": self.headers.get("Content-Type"),
                "body": body,
            }
        )
        if self.path == "/newmoi/workspaces/workspace%201/runtime-image-analysis":
            payload = b'{"answer":"a cat"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path != "/newmoi/workspaces/workspace%201/runtime-artifacts":
            self.send_error(404)
            return
        payload = b'{"file_id":"file-1","original_name":"report.txt","size":3,"md5":"md5","artifact_id":"artifact-1","sha256":"sha256:abc"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.__class__.requests.append(
            {
                "method": "GET",
                "path": self.path,
                "workspace_id": self.headers.get("X-Workspace-ID"),
                "runtime_authorization": self.headers.get("X-MOI-Runtime-Authorization"),
            }
        )
        if self.path != "/newmoi/workspaces/workspace%201/files/file%2F1/download":
            self.send_error(404)
            return
        payload = b"file bytes"
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class RuntimeArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._no_proxy = os.environ.get("NO_PROXY")
        cls._no_proxy_lower = os.environ.get("no_proxy")
        os.environ["NO_PROXY"] = _with_localhost_no_proxy(cls._no_proxy)
        os.environ["no_proxy"] = _with_localhost_no_proxy(cls._no_proxy_lower)
        cls.server = HTTPServer(("127.0.0.1", 0), _RuntimeArtifactHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        if cls._no_proxy is None:
            os.environ.pop("NO_PROXY", None)
        else:
            os.environ["NO_PROXY"] = cls._no_proxy
        if cls._no_proxy_lower is None:
            os.environ.pop("no_proxy", None)
        else:
            os.environ["no_proxy"] = cls._no_proxy_lower

    def setUp(self):
        _RuntimeArtifactHandler.requests = []
        self.client = sdk.Client(
            f"http://127.0.0.1:{self.server.server_port}/newmoi",
            sdk.with_api_key("user-key"),
            sdk.with_runtime_authorization("Bearer runtime-proof"),
        )

    def test_upload_image_analysis_and_download_use_task_scoped_product_sdk_contract(self):
        catalog = self.client.catalog("workspace 1")
        result = catalog.upload_runtime_artifact("report.txt", b"abc")
        self.assertEqual("file-1", result.file_id)
        self.assertEqual("artifact-1", result.artifact_id)
        self.assertEqual("sha256:abc", result.sha256)

        image = catalog.analyze_runtime_image("image.jpg", b"jpeg bytes", "what is shown?")
        self.assertEqual("a cat", image.answer)

        stream = catalog.download_workspace_file("file/1")
        self.addCleanup(stream.close)
        self.assertEqual(b"file bytes", stream.read())

        upload, image_request, download = _RuntimeArtifactHandler.requests
        self.assertEqual("POST", upload["method"])
        self.assertEqual("workspace 1", upload["workspace_id"])
        self.assertEqual("Bearer runtime-proof", upload["runtime_authorization"])
        self.assertTrue(upload["content_type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'filename="report.txt"', upload["body"])
        self.assertIn(b"abc", upload["body"])
        self.assertEqual("POST", image_request["method"])
        self.assertEqual("/newmoi/workspaces/workspace%201/runtime-image-analysis", image_request["path"])
        self.assertEqual("workspace 1", image_request["workspace_id"])
        self.assertEqual("Bearer runtime-proof", image_request["runtime_authorization"])
        self.assertTrue(image_request["content_type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'filename="image.jpg"', image_request["body"])
        self.assertIn(b"question", image_request["body"])
        self.assertIn(b"what is shown?", image_request["body"])
        self.assertIn(b"jpeg bytes", image_request["body"])
        self.assertEqual("GET", download["method"])
        self.assertEqual("workspace 1", download["workspace_id"])
        self.assertEqual("Bearer runtime-proof", download["runtime_authorization"])


if __name__ == "__main__":
    unittest.main()
