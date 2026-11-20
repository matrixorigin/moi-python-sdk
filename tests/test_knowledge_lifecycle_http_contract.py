import base64
import json
from pathlib import Path
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from google.protobuf import json_format
import moi_product_sdk as sdk
from loopback_http import loopback_proxy_environment
from test_catalog_upload_http_contract import read_multipart


def source_selection(value):
    filters = value.get("filters")
    if filters is not None:
        value = dict(value, filters=sdk.SemanticModelSourceSelectionFilters(**filters))
    return sdk.SemanticModelSourceSelectionInput(**value)


def semantic_entry(value):
    return sdk.SemanticEntryInput(
        value["kind"], value["key"], value["spec"], tables=value.get("tables"), domain=value.get("domain", "")
    )


class KnowledgeLifecycleHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("knowledge_lifecycle_http_contract.json")

    def test_governance_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("knowledge_governance_http_contract.json")

    def _run_fixture(self, fixture_name):
        fixture = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / fixture_name
        for scenario in json.loads(fixture.read_text(encoding="utf-8")):
            with self.subTest(scenario=scenario["name"]):
                self._run_scenario(scenario)

    def _run_scenario(self, scenario):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _handle(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                parsed = urllib.parse.urlsplit(self.path)
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
                if scenario.get("multipart") is not None:
                    observed["multipart"] = read_multipart(self.headers["Content-Type"], raw)
                else:
                    observed["body"] = json.loads(raw) if raw else None
                payload = json.dumps(scenario["response"], ensure_ascii=False).encode("utf-8")
                self.send_response(scenario["status"])
                for key, value in scenario.get("response_headers", {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle
            do_PUT = _handle
            do_PATCH = _handle
            do_DELETE = _handle

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        client = sdk.Client(f"http://127.0.0.1:{server.server_port}/newmoi", sdk.with_api_key("synthetic-key"))
        service = client.knowledge("workspace-1")
        input_value = scenario["input"]
        operation = scenario["operation"]
        query = tuple(
            sdk.with_query_values(key, *values)
            for key, values in sorted(scenario.get("query", {}).items())
        )

        try:
            if operation == "list":
                result = service.list(*query)
            elif operation == "list-tags":
                result = service.list_tags(*query)
            elif operation == "create-empty":
                options = []
                if input_value.get("description_present"):
                    options.append(sdk.with_semantic_model_empty_description(input_value["description"]))
                if input_value.get("image_index_enabled_present"):
                    options.append(sdk.with_semantic_model_empty_image_index_enabled(input_value["image_index_enabled"]))
                result = service.create_empty(input_value["name"], *options)
            elif operation == "import-model":
                request = json_format.ParseDict(input_value["request"], sdk.SemanticModelImportRequest())
                result = service.import_model(request)
            elif operation == "import-models":
                requests = [json_format.ParseDict(value, sdk.SemanticModelImportRequest()) for value in input_value["requests"]]
                result = service.import_models(requests)
            elif operation == "upload-local-file":
                result = service.upload_local_file(input_value["filename"], base64.b64decode(input_value["content_base64"]))
            elif operation == "upload-model-local-file":
                result = service.upload_model_local_file(
                    input_value["model_id"], input_value["filename"], base64.b64decode(input_value["content_base64"])
                )
            elif operation == "get":
                result = service.get(input_value["model_id"])
            elif operation == "update":
                options = []
                if input_value.get("description_present"):
                    options.append(sdk.with_semantic_model_description(input_value["description"]))
                result = service.update(input_value["model_id"], input_value["name"], *options)
            elif operation == "delete":
                result = service.delete(input_value["model_id"])
            elif operation == "preview-source-selection-counts":
                result = service.preview_source_selection_counts([source_selection(value) for value in input_value["selections"]])
            elif operation == "preview-model-source-selection-counts":
                result = service.preview_model_source_selection_counts(
                    input_value["model_id"], [source_selection(value) for value in input_value["selections"]]
                )
            elif operation == "list-referencing-agents":
                kwargs = {"cursor": input_value.get("cursor", "")}
                if input_value.get("limit_present"):
                    kwargs["limit"] = input_value["limit"]
                result = service.list_referencing_agents(input_value["model_id"], **kwargs)
            elif operation == "list-source-jobs":
                result = service.list_source_jobs(input_value["model_id"])
            elif operation == "reconcile-source-jobs":
                kwargs = {}
                if input_value.get("retry_present"):
                    kwargs["retry_source_row_id"] = input_value["retry_source_row_id"]
                result = service.reconcile_source_jobs(input_value["model_id"], **kwargs)
            elif operation == "list-sources":
                options = []
                if input_value.get("include_display_status_present"):
                    options.append(sdk.with_query_param("include_display_status", str(input_value["include_display_status"]).lower()))
                result = service.list_sources(input_value["model_id"], *options)
            elif operation == "list-sources-page":
                options = []
                if input_value.get("include_display_status_present"):
                    options.append(sdk.with_query_param("include_display_status", str(input_value["include_display_status"]).lower()))
                result = service.list_sources_page(input_value["model_id"], input_value["page"], input_value["page_size"], *options)
            elif operation == "check-source-existence":
                result = service.check_source_existence(input_value["model_id"], input_value["file_ids"], input_value["table_ids"])
            elif operation == "append-sources":
                selections = None
                if input_value.get("selections_present"):
                    selections = [source_selection(value) for value in input_value["selections"]]
                result = service.append_sources(
                    input_value["model_id"],
                    [sdk.SemanticModelSourceInput(**value) for value in input_value["sources"]],
                    selections=selections,
                )
            elif operation == "backfill-legacy-sources":
                result = service.backfill_legacy_sources(input_value["model_id"])
            elif operation == "search-drawings":
                kwargs = {"drawing_number": input_value.get("drawing_number"), "query": input_value.get("query_text")}
                if input_value.get("top_k_present"):
                    kwargs["top_k"] = input_value["top_k"]
                if input_value.get("filename"):
                    kwargs["query_image_bytes"] = base64.b64decode(input_value["content_base64"])
                    kwargs["query_image_filename"] = input_value["filename"]
                result = service.search_drawings(input_value["knowledge_base_id"], **kwargs)
            elif operation == "get-drawing-provenance":
                kwargs = {}
                if input_value.get("page_number_present"):
                    kwargs["page_number"] = input_value["page_number"]
                result = service.get_drawing_provenance(
                    input_value["knowledge_base_id"], input_value["source_file_id"], **kwargs
                )
            elif operation == "list-entries":
                result = service.list_entries(input_value["model_id"], *query)
            elif operation == "create-entry":
                result = service.create_entry(input_value["model_id"], semantic_entry(input_value["entry"]))
            elif operation == "update-entry":
                result = service.update_entry(
                    input_value["model_id"], input_value["entry_id"], semantic_entry(input_value["entry"])
                )
            elif operation == "delete-entry":
                result = service.delete_entry(input_value["model_id"], input_value["entry_id"])
            elif operation == "export":
                result = service.export(input_value["model_id"])
            elif operation == "import":
                result = service.import_entries(
                    input_value["model_id"], [semantic_entry(value) for value in input_value["entries"]]
                )
            elif operation == "delete-source":
                result = service.delete_source(input_value["model_id"], input_value["source_id"])
            elif operation == "get-source-document":
                result = service.get_source_document(input_value["model_id"], input_value["source_id"], *query)
            elif operation == "update-source-governance":
                options = []
                if input_value.get("tags_present"):
                    options.append(sdk.with_semantic_model_source_tags(*input_value["tags"]))
                if input_value.get("expires_at_present"):
                    options.append(sdk.with_semantic_model_source_expires_at(input_value["expires_at"]))
                if input_value.get("clear_expires_at"):
                    options.append(sdk.with_semantic_model_source_expires_at_cleared())
                if input_value.get("enabled_present"):
                    options.append(sdk.with_semantic_model_source_enabled(input_value["enabled"]))
                if input_value.get("force_enabled_after_expiry_present"):
                    options.append(sdk.with_semantic_model_source_force_enabled_after_expiry(input_value["force_enabled_after_expiry"]))
                result = service.update_source_governance(input_value["model_id"], input_value["source_id"], *options)
            elif operation == "create-segment":
                base = sdk.SemanticModelSegmentBase(input_value["if_match"])
                segment = sdk.SemanticModelSegmentCreateInput(
                    base,
                    level=input_value.get("level", ""),
                    content=input_value.get("content"),
                    ocr_text=input_value.get("ocr_text"),
                    image_description=input_value.get("image_description"),
                    image_file_id=input_value.get("image_file_id", ""),
                    page_image_file_id=input_value.get("page_image_file_id", ""),
                    bbox=input_value.get("bbox"),
                    metadata=input_value.get("metadata"),
                )
                result = service.create_segment(input_value["model_id"], input_value["source_id"], segment)
            elif operation == "update-segment":
                base = sdk.SemanticModelSegmentBase(input_value["if_match"])
                segment = sdk.SemanticModelSegmentUpdateInput(
                    base,
                    content=input_value.get("content"),
                    ocr_text=input_value.get("ocr_text"),
                    image_description=input_value.get("image_description"),
                )
                result = service.update_segment(
                    input_value["model_id"], input_value["source_id"], input_value["segment_id"], segment
                )
            elif operation == "update-segment-enabled":
                base = sdk.SemanticModelSegmentBase(input_value["if_match"])
                result = service.update_segment_enabled(
                    input_value["model_id"], input_value["source_id"], input_value["segment_id"], base, input_value["enabled"]
                )
            elif operation == "delete-segment":
                base = sdk.SemanticModelSegmentBase(input_value["if_match"])
                result = service.delete_segment(
                    input_value["model_id"], input_value["source_id"], input_value["segment_id"], base
                )
            elif operation == "reembed-segments":
                base = sdk.SemanticModelSegmentBase(input_value["if_match"])
                result = service.reembed_segments(input_value["model_id"], input_value["source_id"], base)
            elif operation == "validate":
                result = service.validate(input_value["model_id"])
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400, str(error))
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            if isinstance(result, dict):
                self.assertEqual(result, scenario["response"]["data"])
            else:
                expected = json_format.ParseDict(scenario["response"]["data"], type(result)())
                self.assertEqual(result, expected)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])
        if scenario.get("multipart") is not None:
            self.assertEqual(observed["multipart"], scenario["multipart"])
        else:
            self.assertEqual(observed["body"], scenario["request"])


if __name__ == "__main__":
    unittest.main()
