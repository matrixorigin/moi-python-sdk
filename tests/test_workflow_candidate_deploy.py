import json
import unittest
from pathlib import Path
from typing import Any

import moi_product_sdk.client as sdk_client


_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "go-sdk" / "testdata" / "workflow_candidate_deploy_body.json"


def _acceptance_data(
    *,
    task_id: str = "task-123",
    artifact_id: str = "workflow_candidate_0123456789abcdef0123456789abcdef",
) -> dict[str, Any]:
    return {
        "candidate_ref": {"task_id": task_id, "artifact_id": artifact_id},
        "accepted_at": "2026-08-07T12:00:00Z",
        "candidate": {
            "ok": True,
            "candidate_id": artifact_id,
            "workflow": {"name": "accepted"},
            "runtime_fields": {"fields": []},
            "runtime_layout": {"groups": []},
            "catalog_revision": "catalog-1",
            "snapshot_digest": "snapshot-sha256",
            "syntax_version": "v1",
            "compiler_version": "compiler-1",
            "source_digest": "source-sha256",
            "artifact_digest": "artifact-sha256",
            "envelope_digest": "envelope-sha256",
            "source_code": "package workflow",
        },
    }


def _accepted_candidate() -> sdk_client.AcceptedWorkflowCandidate:
    return sdk_client.accepted_workflow_candidate_from_acceptance(
        sdk_client._workflow_candidate_acceptance(_acceptance_data())
    )


class WorkflowCandidateDeployContractTest(unittest.TestCase):
    def test_candidate_body_matches_cross_sdk_fixture(self):
        accepted_candidate = _accepted_candidate()
        body = sdk_client._workflow_candidate_deploy_body(
            "candidate workflow",
            accepted_candidate,
            (
                sdk_client.with_workflow_id("workflow-1"),
                sdk_client.with_workflow_description("server-owned candidate"),
                sdk_client.with_workflow_execution_mode("volume_trigger"),
                sdk_client.with_workflow_source_type("nl2dsl"),
                sdk_client.with_workflow_volume_trigger(
                    7,
                    True,
                    '{"source":"volume-7"}',
                ),
                sdk_client.with_workflow_default_values(
                    {"enabled": True, "limit": 7}
                ),
                sdk_client.with_workflow_compute_resource_id("compute-1"),
            ),
        )

        with _FIXTURE_PATH.open(encoding="utf-8") as fixture:
            self.assertEqual(body, json.load(fixture))

        forbidden = {
            "dsl_yaml",
            "runtime_fields",
            "runtime_layout",
            "input_form",
            "form_layout",
            "design_graph",
            "candidate_id",
            "source_digest",
            "artifact_digest",
            "envelope_digest",
            "catalog_revision",
            "catalog_snapshot_digest",
            "snapshot_digest",
            "source_code",
            "syntax_version",
            "compiler_version",
        }
        self.assertTrue(forbidden.isdisjoint(body), body)

    def test_candidate_ref_rejects_missing_identity(self):
        for task_id, artifact_id in (
            ("", "workflow_candidate_0123456789abcdef0123456789abcdef"),
            ("task-123", ""),
        ):
            with self.subTest(task_id=task_id, artifact_id=artifact_id):
                with self.assertRaises(ValueError):
                    sdk_client.WorkflowCandidateRef(task_id, artifact_id)

    def test_candidate_body_rejects_client_form_layout_and_legacy_source(self):
        accepted_candidate = _accepted_candidate()
        rejected_options = (
            sdk_client.with_workflow_mowl({"name": "replacement"}),
            sdk_client.with_workflow_input_form({"fields": []}),
            sdk_client.with_workflow_form_layout({"groups": []}),
            sdk_client.with_workflow_source_type("agent"),
        )
        for option in rejected_options:
            with self.subTest(option=option):
                with self.assertRaises(ValueError):
                    sdk_client._workflow_candidate_deploy_body(
                        "candidate workflow",
                        accepted_candidate,
                        (option,),
                    )

    def test_explicit_accept_then_typed_deploy_uses_exact_server_handoff(self):
        calls: list[tuple[str, str, str, object]] = []

        class FakeClient:
            def _request(self, method, path, workspace_id, body, require_envelope=False):
                calls.append((method, path, workspace_id, body))
                if path == "/workflow/v2/workflow-candidates/accept":
                    return _acceptance_data()
                return {}

        service = sdk_client.WorkflowService(FakeClient(), "workspace-1")
        candidate_ref = sdk_client.WorkflowCandidateRef(
            "task-123",
            "workflow_candidate_0123456789abcdef0123456789abcdef",
        )

        accepted = service.accept_candidate(candidate_ref, sdk_client.WorkflowCandidateConfirmation(proposal_id="proposal-1", idempotency_key="confirm-1"))
        service.deploy_candidate("candidate workflow", accepted)

        self.assertIsInstance(accepted, sdk_client.AcceptedWorkflowCandidate)
        self.assertEqual(accepted.candidate_ref.to_dict(), candidate_ref.to_dict())
        self.assertEqual(
            calls[0],
            (
                "POST",
                "/workflow/v2/workflow-candidates/accept",
                "workspace-1",
                {"candidate_ref": candidate_ref.to_dict(), "proposal_id": "proposal-1", "idempotency_key": "confirm-1"},
            ),
        )
        self.assertEqual(calls[1][1], "/workflow/v2/workflow-deployments")
        self.assertEqual(
            calls[1][3],
            {
                "name": "candidate workflow",
                "source_type": "nl2dsl",
                "candidate_ref": candidate_ref.to_dict(),
            },
        )

    def test_candidate_deploy_rejects_bare_pending_ref(self):
        candidate_ref = sdk_client.WorkflowCandidateRef(
            "task-123",
            "workflow_candidate_0123456789abcdef0123456789abcdef",
        )
        with self.assertRaises(TypeError):
            sdk_client._workflow_candidate_deploy_body(
                "candidate workflow",
                candidate_ref,
                (),
            )

    def test_accepted_candidate_rejects_malformed_server_facts(self):
        malformed = []

        missing_accepted_at = _acceptance_data()
        missing_accepted_at["accepted_at"] = ""
        malformed.append(missing_accepted_at)

        mismatched_candidate = _acceptance_data()
        mismatched_candidate["candidate"]["candidate_id"] = "workflow_candidate_other"
        malformed.append(mismatched_candidate)

        missing_workflow = _acceptance_data()
        missing_workflow["candidate"].pop("workflow")
        malformed.append(missing_workflow)

        for value in malformed:
            with self.subTest(value=value):
                acceptance = sdk_client._workflow_candidate_acceptance(value)
                with self.assertRaises(ValueError):
                    sdk_client.accepted_workflow_candidate_from_acceptance(acceptance)

    def test_raw_deployment_escape_hatches_are_removed(self):
        self.assertFalse(hasattr(sdk_client.WorkflowService, "deploy_raw"))
        self.assertFalse(hasattr(sdk_client.WorkflowService, "deploy_raw_result"))

    def test_manual_deploy_body_remains_separate(self):
        body = sdk_client._workflow_deploy_body(
            "manual workflow",
            "workflow:\n  name: manual\n",
            (
                sdk_client.with_workflow_source_type("manual_dsl"),
                sdk_client.with_workflow_input_form({"fields": []}),
                sdk_client.with_workflow_form_layout({"groups": []}),
                sdk_client.with_workflow_http_notification("http://callback.test/completed", "COMPLETED", "FAILED", "CANCELLED"),
            ),
        )

        self.assertEqual(body["source_type"], "manual_dsl")
        self.assertEqual(body["dsl_yaml"], "workflow:\n  name: manual\n")
        self.assertIn("runtime_fields", body)
        self.assertIn("runtime_layout", body)
        self.assertNotIn("candidate_ref", body)
        self.assertEqual(body["notification_config"], {
            "type": "http", "url": "http://callback.test/completed",
            "notify_workflow_states": ["COMPLETED", "FAILED", "CANCELLED"],
        })

    def test_manual_deploy_rejects_candidate_source_type(self):
        with self.assertRaises(ValueError):
            sdk_client._workflow_deploy_body(
                "manual workflow",
                "workflow:\n  name: manual\n",
                (sdk_client.with_workflow_source_type("nl2dsl"),),
            )

    def test_dynamic_service_ui_resource_binds_html_file(self):
        binding = {"file_id": "file-html", "mime_type": "text/html"}
        deploy_body = sdk_client._workflow_deploy_body(
            "api workflow",
            "workflow:\n  name: api\n",
            (
                sdk_client.with_workflow_execution_mode("dynamic_service"),
                sdk_client.with_workflow_dynamic_service("echo", ui_resource=binding),
            ),
        )
        self.assertEqual(deploy_body["dynamic_service"]["ui_resource"], binding)

        update_body = sdk_client._workflow_update_body(
            (sdk_client.with_workflow_update_dynamic_service("echo", ui_resource=binding),),
        )
        self.assertEqual(update_body["dynamic_service"]["ui_resource"], binding)

        unbound_body = sdk_client._workflow_deploy_body(
            "api workflow",
            "workflow:\n  name: api\n",
            (sdk_client.with_workflow_dynamic_service("echo"),),
        )
        self.assertNotIn("ui_resource", unbound_body["dynamic_service"])


    def test_history_restore_and_reject_use_typed_routes(self):
        calls: list[tuple[str, str, str, object]] = []

        class FakeClient:
            def _request(self, method, path, workspace_id, body=None, require_envelope=False):
                calls.append((method, path, workspace_id, body))
                if path.startswith("/workflow/v2/workflow-candidates/history"):
                    return {"items": [], "total_tasks": 0, "limit": 20, "offset": 0}
                if path == "/workflow/v2/workflow-candidates/restore":
                    return {"id": "restore-1", "candidate_ref": {"task_id": "task-1", "artifact_id": "candidate-1"}, "candidate": {"ok": True}, "status": "pending", "created_at": "2026-08-31T00:00:00Z"}
                return {"proposal_id": "proposal-1", "status": "rejected"}

        service = sdk_client.WorkflowService(FakeClient(), "workspace-1")
        page = service.history("context-1", 20, 0)
        restored = service.restore_history(sdk_client.WorkflowHistoryRestoreRequest(context_id="context-1", request_id="restore-1", candidate_ref=sdk_client.WorkflowCandidateRef("task-1", "candidate-1")))
        rejected = service.reject_candidate_proposal("proposal-1")
        self.assertEqual(page.limit, 20)
        self.assertEqual(restored.id, "restore-1")
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(calls[0][1], "/workflow/v2/workflow-candidates/history?context_id=context-1&limit=20&offset=0")
        self.assertEqual(calls[1][3], {"context_id": "context-1", "request_id": "restore-1", "candidate_ref": {"task_id": "task-1", "artifact_id": "candidate-1"}})
        self.assertEqual(calls[2][3], {"proposal_id": "proposal-1"})


if __name__ == "__main__":
    unittest.main()
