import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf.struct_pb2 import Value
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment


class ResourceTagsTest(unittest.TestCase):
    def test_unassigned_filter_and_bounded_assignment_read_use_typed_contracts(self):
        self.enterContext(loopback_proxy_environment())
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, payload, self.headers))
                if self.path.endswith("/groups/query"):
                    data = {"tag": {"id": "tag", "name": "Environment", "type": "workflow"},
                            "items": [{"value_id": None, "value": None, "resource_count": 2}], "total": 1}
                else:
                    data = {"items": [{"resource_id": "workflow", "tags": [
                        {"tag_id": "tag", "tag_name": "Environment", "value_id": "test", "value": "Test"}]}]}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"code": "OK", "data": data}).encode())

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("fixture-key"))
            tags = client.resource_tags("workspace")
            grouped = tags.groups(sdk.ResourceTagQueryRequest(
                type="workflow", group_by="environment", include_dynamic_service=True, limit=20,
                filters=[sdk.ResourceTagFilter(tag_id="business", value_id=Value(null_value=0))],
            ))
            self.assertEqual(("tag", "Environment", 1), (grouped.tag.id, grouped.tag.name, grouped.total))
            self.assertFalse(grouped.items[0].HasField("value_id"))
            self.assertEqual(2, grouped.items[0].resource_count)
            result = tags.assignments(sdk.ResourceTagAssignmentsRequest(type="workflow", resource_ids=["workflow"], tag_ids=["tag"]))
            self.assertEqual(("workflow", "tag", "test"), (result.items[0].resource_id, result.items[0].tags[0].tag_id, result.items[0].tags[0].value_id))
            self.assertEqual("/newmoi/tags/groups/query", requests[0][0])
            self.assertEqual([{"tag_id": "business", "value_id": None}], requests[0][1]["filters"])
            self.assertTrue(requests[0][1]["include_dynamic_service"])
            self.assertEqual(("/newmoi/tags/resources/tags/query", {"type": "workflow", "resource_ids": ["workflow"], "tag_ids": ["tag"]}), requests[1][:2])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
