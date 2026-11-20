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


def workflow_execution_options(request, run=False):
    options = []
    for name in sorted(request):
        value = request[name]
        if name == "values":
            helper = sdk.with_workflow_run_values if run else sdk.with_workflow_rerun_values
        elif name == "replace_saved_defaults":
            helper = sdk.with_workflow_run_replace_saved_defaults if run else sdk.with_workflow_retry_replace_saved_defaults
        elif name == "trigger_now":
            helper = sdk.with_workflow_run_trigger_now if run else sdk.with_workflow_rerun_trigger_now
        elif name == "config_override":
            helper = sdk.with_workflow_rerun_config_override
        elif name == "expected_rerun_contract_hash":
            helper = sdk.with_expected_workflow_rerun_contract_hash
        elif name == "reason":
            helper = sdk.with_workflow_rerun_reason
        else:
            raise AssertionError(f"unknown execution option {name}")
        options.append(helper(value))
    return options


def workflow_cancel_options(request):
    return [sdk.with_workflow_cancel_reason(request["reason"])] if "reason" in request else []


def lineage_revision_options(request):
    return [getattr(sdk, "with_lineage_" + name)(request[name]) for name in sorted(request)]


def lineage_switch_options(request):
    switches = [sdk.LineageRevisionSwitch(**value) for value in request["switches"]]
    options = []
    if "expected_effective_set_version" in request:
        options.append(sdk.with_lineage_switch_expected_effective_set_version(request["expected_effective_set_version"]))
    return switches, options


def lineage_rerun_options(request):
    return [getattr(sdk, "with_lineage_rerun_" + name)(request[name]) for name in sorted(request)]


def lineage_revision_rerun_options(request):
    options = []
    for name in sorted(request):
        if name == "selected_revisions_json":
            helper = sdk.with_lineage_selected_revisions_json
        else:
            helper = getattr(sdk, "with_lineage_revision_rerun_" + name)
        options.append(helper(request[name]))
    return options


class WorkflowVersionHTTPContractTest(unittest.TestCase):
    def test_shared_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_versions_http_contract.json")

    def test_app_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_apps_http_contract.json")

    def test_candidate_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_candidates_http_contract.json")

    def test_resource_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_resources_http_contract.json")

    def test_execution_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_executions_http_contract.json")

    def test_lineage_http_contracts(self):
        self.enterContext(loopback_proxy_environment())
        self._run_fixture("workflow_lineage_http_contract.json")

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
                multipart = read_multipart(self.headers["Content-Type"], raw) if scenario.get("multipart") else None
                observed.update(
                    method=self.command,
                    path=parsed.path,
                    query=urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                    body=None if multipart else (json.loads(raw) if raw else None),
                    multipart=multipart,
                    workspace=self.headers.get("X-Workspace-ID"),
                    api_key=self.headers.get("X-API-Key"),
                    authorization=self.headers.get("Authorization"),
                    cookie=self.headers.get("Cookie"),
                )
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
        service = client.workflows("workspace-1")
        input_value = scenario["input"]
        operation = scenario["operation"]
        query = tuple(
            sdk.with_query_values(key, *values)
            for key, values in sorted(scenario.get("query", {}).items())
        )
        try:
            if operation == "workflow-templates":
                result = service.workflow_templates()
            elif operation == "delete-workflow-template":
                result = service.delete_workflow_template(input_value["template_id"])
            elif operation == "versions":
                result = service.versions(input_value["workflow_id"])
            elif operation == "create-version":
                request = json_format.ParseDict(input_value["request"], sdk.WorkflowVersionCreateRequest())
                result = service.create_version(input_value["workflow_id"], request)
            elif operation == "version-by-number":
                result = service.version_by_number(input_value["workflow_id"], input_value["number"])
            elif operation == "latest-published-version":
                result = service.latest_published_version(input_value["workflow_id"])
            elif operation == "version":
                result = service.version(input_value["workflow_id"], input_value["version_id"])
            elif operation == "publish-version":
                result = service.publish_version(input_value["workflow_id"], input_value["version_id"])
            elif operation == "deprecate-version":
                result = service.deprecate_version(input_value["workflow_id"], input_value["version_id"])
            elif operation == "delete-version":
                result = service.delete_version(input_value["workflow_id"], input_value["version_id"])
            elif operation == "apps":
                result = service.apps(*query)
            elif operation == "list":
                result = service.list(*query)
            elif operation == "get":
                result = service.get(input_value["workflow_id"])
            elif operation == "update":
                options = []
                for key, factory in (
                    ("name", sdk.with_workflow_update_name),
                    ("description", sdk.with_workflow_update_description),
                    ("execution_mode", sdk.with_workflow_update_execution_mode),
                    ("cron_expression", sdk.with_workflow_update_cron_expression),
                    ("dsl_yaml", sdk.with_workflow_update_dsl_yaml),
                ):
                    if input_value.get(key + "_present"):
                        options.append(factory(input_value[key]))
                if "runtime_fields" in input_value:
                    options.append(sdk.with_workflow_update_input_form(input_value["runtime_fields"]))
                if "runtime_layout" in input_value:
                    options.append(sdk.with_workflow_update_form_layout(input_value["runtime_layout"]))
                if "default_values" in input_value:
                    options.append(sdk.with_workflow_update_default_values(input_value["default_values"]))
                if "volume_trigger" in input_value:
                    options.append(sdk.with_workflow_update_volume_trigger(**input_value["volume_trigger"]))
                if "dynamic_service" in input_value:
                    options.append(sdk.with_workflow_update_dynamic_service(**input_value["dynamic_service"]))
                result = service.update(input_value["workflow_id"], *options)
            elif operation == "delete":
                result = service.delete(input_value["workflow_id"])
            elif operation == "get-dispatch-job":
                result = service.get_dispatch_job(input_value["workflow_id"], input_value["dispatch_job_id"])
            elif operation in ("enable", "pause", "resume"):
                result = getattr(service, operation)(input_value["workflow_id"])
            elif operation == "submit-candidate":
                request = json_format.ParseDict(input_value["request"], sdk.WorkflowCandidateSubmitRequest())
                result = service.submit_candidate(request)
            elif operation == "test-candidate":
                request = json_format.ParseDict(input_value["request"], sdk.WorkflowCandidateTestRequest())
                result = service.test_candidate(request)
            elif operation == "accept-candidate":
                candidate_ref = sdk.WorkflowCandidateRef(input_value["task_id"], input_value["artifact_id"])
                confirmation = sdk.WorkflowCandidateConfirmation(
                    proposal_id=input_value["proposal_id"], idempotency_key=input_value["idempotency_key"]
                )
                result = service.accept_candidate(candidate_ref, confirmation)
            elif operation == "history":
                result = service.history(input_value["context_id"], input_value["limit"], input_value["offset"])
            elif operation == "restore-history":
                parent_ref = None
                if input_value.get("parent_task_id") or input_value.get("parent_artifact_id"):
                    parent_ref = sdk.WorkflowCandidateRef(input_value["parent_task_id"], input_value["parent_artifact_id"])
                request = sdk.WorkflowHistoryRestoreRequest(
                    context_id=input_value["context_id"],
                    request_id=input_value["request_id"],
                    candidate_ref=sdk.WorkflowCandidateRef(input_value["task_id"], input_value["artifact_id"]),
                    parent_ref=parent_ref,
                )
                result = service.restore_history(request)
            elif operation == "reject-candidate-proposal":
                result = service.reject_candidate_proposal(input_value["proposal_id"])
            elif operation == "deploy":
                options = []
                if input_value.get("description_present"):
                    options.append(sdk.with_workflow_description(input_value["description"]))
                result = service.deploy(input_value["name"], input_value["dsl_yaml"], *options)
            elif operation == "deploy-candidate":
                acceptance = json_format.ParseDict(input_value["acceptance"], sdk.WorkflowCandidateAcceptance())
                accepted = sdk.AcceptedWorkflowCandidate(acceptance)
                options = []
                if input_value.get("description_present"):
                    options.append(sdk.with_workflow_description(input_value["description"]))
                result = service.deploy_candidate(input_value["name"], accepted, *options)
            elif operation == "custom-operators":
                result = service.custom_operators(*query)
            elif operation == "create-custom-operator":
                request = input_value["request"]
                spec = sdk.CustomOperatorSpec(
                    name=request["name"],
                    identifier=request["identifier"],
                    description=request["description"],
                    input_schema=request["input_schema"],
                    output_schema=request["output_schema"],
                )
                required = {"name", "identifier", "description", "input_schema", "output_schema"}
                options = [
                    getattr(sdk, "with_custom_operator_" + name)(request[name])
                    for name in sorted(request)
                    if name not in required
                ]
                result = service.create_custom_operator(spec, *options)
            elif operation == "get-custom-operator-source":
                result = service.get_custom_operator_source(
                    input_value["node_id"], input_value["version"], input_value["task_id"]
                )
            elif operation == "delete-custom-operator":
                result = service.delete_custom_operator(input_value["operator_id"])
            elif operation == "get-custom-operator":
                result = service.get_custom_operator(input_value["operator_id"])
            elif operation == "update-custom-operator":
                request = input_value["request"]
                options = [
                    getattr(sdk, "with_custom_operator_update_" + name)(request[name])
                    for name in sorted(request)
                ]
                result = service.update_custom_operator(input_value["operator_id"], *options)
            elif operation == "get-custom-operator-code":
                result = service.get_custom_operator_code(input_value["operator_id"])
            elif operation in ("disable-custom-operator", "enable-custom-operator"):
                method = "disable_custom_operator" if operation == "disable-custom-operator" else "enable_custom_operator"
                result = getattr(service, method)(input_value["operator_id"])
            elif operation == "test-custom-operator":
                request = input_value["request"]
                values = {"input": request["input"]}
                if "wait_timeout_seconds" in request:
                    values["wait_timeout_seconds"] = request["wait_timeout_seconds"]
                result = service.test_custom_operator(
                    input_value["operator_id"], sdk.CustomOperatorTestInput(**values)
                )
            elif operation == "invoke-workflow-dynamic-service":
                request = input_value["request"]
                values = {
                    key: request[key]
                    for key in ("version", "version_number", "trace")
                    if key in request
                }
                result = service.invoke_workflow_dynamic_service(
                    sdk.DynamicServiceInvokeSpec(
                        request["service_name"],
                        request["payload"],
                        files=(
                            [("file", input_value["filename"], base64.b64decode(input_value["content_base64"]))]
                            if input_value.get("filename")
                            else None
                        ),
                        **values,
                    )
                )
            elif operation in ("ensure-test-scratch", "observe-test-scratch"):
                request = json_format.ParseDict(input_value["request"], sdk.WorkflowScratchScope())
                method = "ensure_test_scratch" if operation == "ensure-test-scratch" else "observe_test_scratch"
                result = getattr(service, method)(request)
            elif operation == "reset-test-scratch":
                result = service.reset_test_scratch(input_value["task_id"])
            elif operation == "workitem-catalog":
                result = service.workitem_catalog()
            elif operation == "workitem-catalog-item":
                result = service.workitem_catalog_item(input_value["node_id"])
            elif operation == "get-workitem-api-service":
                result = service.get_workitem_api_service(input_value["node_id"], input_value["version"])
            elif operation == "publish-workitem-api-service":
                result = service.publish_workitem_api_service(
                    input_value["node_id"], sdk.WorkitemAPIServicePublishSpec(**input_value["request"])
                )
            elif operation in ("disable-workitem-api-service", "enable-workitem-api-service"):
                method = "disable_workitem_api_service" if operation == "disable-workitem-api-service" else "enable_workitem_api_service"
                result = getattr(service, method)(input_value["node_id"], input_value["version"])
            elif operation == "invoke-workitem-api-service":
                result = service.invoke_workitem_api_service(
                    input_value["node_id"], sdk.WorkitemAPIServiceInvokeSpec(**input_value["request"])
                )
            elif operation == "list-all-runs":
                result = service.list_all_runs(*query)
            elif operation == "get-run-by-id":
                result = service.get_run_by_id(input_value["execution_id"])
            elif operation == "get-run-import-context-by-id":
                result = service.get_run_import_context_by_id(input_value["execution_id"])
            elif operation == "list-run-import-files-by-id":
                result = service.list_run_import_files_by_id(input_value["execution_id"], *query)
            elif operation == "get-run-node-by-id":
                result = service.get_run_node_by_id(input_value["execution_id"], input_value["node_key"])
            elif operation == "get-run-result-by-id":
                result = service.get_run_result_by_id(input_value["execution_id"])
            elif operation == "list-file-executions":
                result = service.list_file_executions(*query)
            elif operation == "list-runs":
                result = service.list_runs(input_value["workflow_id"], *query)
            elif operation == "run":
                result = service.run(input_value["workflow_id"], *workflow_execution_options(input_value["request"], run=True))
            elif operation == "batch-retry-failed-files":
                result = service.batch_retry_failed_files(
                    input_value["workflow_id"], input_value["source_dispatch_job_id"],
                    input_value["execution_ids"], input_value["all_failed"], input_value["request_id"],
                )
            elif operation == "delete-run":
                result = service.delete_run(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "get-run":
                result = service.get_run(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "cancel-run":
                result = service.cancel_run(
                    input_value["workflow_id"], input_value["execution_id"],
                    *workflow_cancel_options(input_value["request"]),
                )
            elif operation == "get-run-import-context":
                result = service.get_run_import_context(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "list-run-import-files":
                result = service.list_run_import_files(input_value["workflow_id"], input_value["execution_id"], *query)
            elif operation == "get-run-node":
                result = service.get_run_node(input_value["workflow_id"], input_value["execution_id"], input_value["node_key"])
            elif operation == "get-run-node-rerun-plan":
                result = service.get_run_node_rerun_plan(
                    input_value["workflow_id"], input_value["execution_id"], input_value["node_key"], *query,
                )
            elif operation == "create-run-node-rerun":
                result = service.create_run_node_rerun(
                    input_value["workflow_id"], input_value["execution_id"], input_value["node_key"],
                    input_value["mode"], input_value["source_node_execution_id"],
                    *workflow_execution_options(input_value["request"]),
                )
            elif operation in ("pause-run", "refresh-run", "resume-run"):
                method = operation.replace("-", "_")
                result = getattr(service, method)(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "list-run-rerun-branches":
                result = service.list_run_rerun_branches(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "get-run-rerun":
                result = service.get_run_rerun(input_value["workflow_id"], input_value["execution_id"], input_value["rerun_id"])
            elif operation == "cancel-run-rerun":
                result = service.cancel_run_rerun(
                    input_value["workflow_id"], input_value["execution_id"], input_value["rerun_id"],
                    *workflow_cancel_options(input_value["request"]),
                )
            elif operation == "get-run-result":
                result = service.get_run_result(input_value["workflow_id"], input_value["execution_id"])
            elif operation == "retry-run":
                result = service.retry_run(
                    input_value["workflow_id"], input_value["execution_id"],
                    *workflow_execution_options(input_value["request"]),
                )
            elif operation == "artifact-block-revisions":
                result = service.artifact_block_revisions(input_value["artifact_id"], input_value["block_id"])
            elif operation == "create-artifact-block-revision":
                result = service.create_artifact_block_revision(
                    input_value["artifact_id"], input_value["block_id"],
                    *lineage_revision_options(input_value["request"]),
                )
            elif operation == "switch-artifact-effective-revisions":
                switches, options = lineage_switch_options(input_value["request"])
                result = service.switch_artifact_effective_revisions(input_value["artifact_id"], switches, *options)
            elif operation == "artifact-node":
                result = service.artifact_node(input_value["artifact_id"], input_value["node_id"])
            elif operation == "artifact-node-block-revisions":
                result = service.artifact_node_block_revisions(
                    input_value["artifact_id"], input_value["node_id"], input_value["block_id"],
                )
            elif operation == "create-artifact-node-block-revision":
                result = service.create_artifact_node_block_revision(
                    input_value["artifact_id"], input_value["node_id"], input_value["block_id"],
                    *lineage_revision_options(input_value["request"]),
                )
            elif operation == "switch-artifact-node-effective-revisions":
                switches, options = lineage_switch_options(input_value["request"])
                result = service.switch_artifact_node_effective_revisions(
                    input_value["artifact_id"], input_value["node_id"], switches, *options,
                )
            elif operation == "artifact-node-output-blocks":
                result = service.artifact_node_output_blocks(input_value["artifact_id"], input_value["node_id"])
            elif operation == "create-target-artifact-node-revision-rerun":
                result = service.create_target_artifact_node_revision_rerun(
                    input_value["artifact_id"], input_value["node_id"], input_value["target_output_emission_id"],
                    *lineage_revision_rerun_options(input_value["request"]),
                )
            elif operation == "create-artifact-node-rerun":
                result = service.create_artifact_node_rerun(
                    input_value["artifact_id"], input_value["node_id"],
                    *lineage_rerun_options(input_value["request"]),
                )
            elif operation == "artifact-output-blocks":
                result = service.artifact_output_blocks(input_value["artifact_id"])
            elif operation == "artifact-lineage-overview":
                result = service.artifact_lineage_overview(input_value["artifact_id"])
            elif operation == "catalog-file-lineage-overview":
                result = service.catalog_file_lineage_overview(input_value["file_id"], *query)
            else:
                self.fail(f"unknown operation {operation}")
        except sdk.Error as error:
            self.assertGreaterEqual(scenario["status"], 400)
            self.assertEqual(error.code, scenario["response"]["code"])
            self.assertEqual(error.message, scenario["response"]["msg"])
            self.assertEqual(error.status, scenario["status"])
            self.assertEqual(error.request_id, scenario.get("response_headers", {}).get("X-Request-ID", ""))
        else:
            self.assertLess(scenario["status"], 400)
            if operation == "delete-version":
                self.assertIsNone(result)
            elif operation == "apps":
                self.assertEqual(result, scenario["response"]["data"])
            elif operation == "accept-candidate":
                expected = json_format.ParseDict(scenario["response"]["data"], sdk.WorkflowCandidateAcceptance())
                self.assertEqual(result.acceptance, expected)
            elif operation == "workflow-templates":
                expected = json_format.ParseDict({"templates": scenario["response"]["data"]}, sdk.WorkflowTemplateList())
                self.assertEqual(result, expected)
            elif operation == "workitem-catalog-item":
                expected = json_format.ParseDict({"item": scenario["response"]["data"]}, sdk.WorkitemCatalogDetail())
                self.assertEqual(result, expected)
            elif isinstance(result, sdk.DynamicServiceInvokeResult):
                expected = sdk.DynamicServiceInvokeResult(scenario["response"]["data"])
                self.assertEqual(vars(result), vars(expected))
            else:
                expected = json_format.ParseDict(scenario["response"]["data"], type(result)())
                self.assertEqual(result, expected)

        self.assertEqual(observed["method"], scenario["method"])
        self.assertEqual(observed["path"], scenario["path"])
        self.assertEqual(observed["query"], scenario.get("query", {}))
        self.assertEqual(observed["body"], scenario["request"])
        self.assertEqual(observed["multipart"], scenario.get("multipart"))
        self.assertEqual(observed["workspace"], "workspace-1")
        self.assertEqual(observed["api_key"], "synthetic-key")
        self.assertIsNone(observed["authorization"])
        self.assertIsNone(observed["cookie"])


if __name__ == "__main__":
    unittest.main()
