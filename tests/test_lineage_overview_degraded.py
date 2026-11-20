import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


_DEGRADED_OVERVIEW = b"""{
  "code": "OK",
  "msg": "OK",
  "data": {
    "artifact": {
      "artifact_id": "root-1:case-1",
      "root_asset_id": "root-1",
      "stage_asset_id": "",
      "case_id": "case-1",
      "workflow_version_id": "",
      "raw_file_id": "raw-1",
      "parsed_file_id": "parsed-1",
      "parsed_file_available": true,
      "origin_file_name": "doc.md",
      "origin_file_ext": "md",
      "selected_by": "entry_case_id",
      "selection_metadata": {"entry_case_id": "case-1"},
      "source_status": "unavailable",
      "source_unavailable_reason": "execution_context_missing",
      "case_candidates": [
        {"case_id": "case-1", "created_at": "2026-10-17T16:00:00Z", "status": "source_unavailable", "role": "producer", "selected": true}
      ]
    },
    "topology": {"nodes": [], "edges": []},
    "entry": {"catalog_file_id": "parsed-1", "volume_id": "8"}
  }
}"""


class LineageOverviewDegradedContractTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_catalog_file_lineage_overview_decodes_source_unavailable(self):
        # The SDK parses responses with ignore_unknown_fields=False, so the
        # degraded overview (deleted producer workflow) must decode via the
        # generated proto fields source_status/source_unavailable_reason.
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("X-Request-ID", "lineage-degraded")
                self.end_headers()
                self.wfile.write(_DEGRADED_OVERVIEW)

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}", sdk.with_api_key("user-key"))
            overview = client.workflows("workspace").catalog_file_lineage_overview("parsed-1")
            self.assertEqual("unavailable", overview.artifact.source_status)
            self.assertEqual("execution_context_missing", overview.artifact.source_unavailable_reason)
            self.assertEqual("entry_case_id", overview.artifact.selected_by)
            self.assertEqual("source_unavailable", overview.artifact.case_candidates[0].status)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
