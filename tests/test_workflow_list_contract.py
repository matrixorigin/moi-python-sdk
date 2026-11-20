import copy
import json
import pathlib
import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[2] / "go-sdk" / "testdata"


# GET /workflow/v2/workflow-apps -> WorkflowListEnvelope strict-decode contract.
class WorkflowListContractTest(unittest.TestCase):
    def test_response_permissions_do_not_change_strict_business_data(self):
        data = {"total": 37, "workflows": [self._fixture("workflow_list_manual_ready.json")]}
        plain = sdk_client._workflow_list_envelope(data)
        wire = {
            "code": "OK", "data": data,
            "permissions": {"workspace_id": "workspace", "effective_role_id": "role", "resources": [
                {"resource_type": "workflow", "resource_id": "id", "allowed_actions": ["workflow.run"]}
            ]},
        }
        decoded = sdk_client._workflow_list_envelope(sdk_client._parse_response(json.dumps(wire).encode(), ""))
        self.assertEqual(plain, decoded)
        business = copy.deepcopy(data)
        business["workflows"][0]["allowed_actions"] = ["workflow.run"]
        with self.assertRaises(sdk.Error):
            sdk_client._workflow_list_envelope(business)

    def test_published_invocation_schemas(self):
        for schemas in ({}, {
            "input_schema": '{"type":"object","properties":{"query":{"type":"string"}}}',
            "output_schema": '{"type":"object","properties":{"answer":{"type":"string"}}}',
        }):
            with self.subTest(schemas=schemas):
                workflow = self._fixture("workflow_list_manual_ready.json")
                workflow["trigger_summary"] = {
                    "mode": "api", "service_name": "published-api", **schemas,
                }
                result = sdk_client._workflow_list_envelope({"total": 1, "workflows": [workflow]})
                trigger = result.workflows[0].trigger_summary
                self.assertEqual(trigger.service_name, "published-api")
                self.assertEqual(trigger.input_schema, schemas.get("input_schema", ""))
                self.assertEqual(trigger.output_schema, schemas.get("output_schema", ""))

    def test_list_decodes_backend_fixtures_strictly(self):
        for name in (
            "workflow_list_manual_ready.json",
            "workflow_list_cron_scheduled.json",
            "workflow_list_dynamic_service.json",
            "workflow_list_dynamic_service_ready.json",
        ):
            with self.subTest(fixture=name):
                result = sdk_client._workflow_list_envelope(
                    {"total": 1, "workflows": [self._fixture(name)]}
                )
                self.assertEqual(len(result.workflows), 1)
                self.assertEqual(result.total, 1)
                self._assert_workflow(result.workflows[0], name)

    def test_detail_preserves_dynamic_service_schemas(self):
        result = sdk_client._workflow_envelope(
            {"workflow": self._fixture("workflow_list_dynamic_service_ready.json")}
        )
        self._assert_dynamic_service_schemas(result.workflow.trigger_summary)

    def test_list_rejects_unknown_fields(self):
        workflow = self._fixture("workflow_list_manual_ready.json")
        workflow["unregistered_field"] = True
        with self.assertRaisesRegex(sdk.Error, "unregistered_field"):
            sdk_client._workflow_list_envelope({"total": 1, "workflows": [workflow]})

    def _assert_workflow(self, workflow, fixture_name):
        self.assertTrue(workflow.id)
        self.assertTrue(workflow.name)
        self.assertTrue(workflow.HasField("created_at"))
        self.assertTrue(workflow.HasField("updated_at"))
        if fixture_name == "workflow_list_manual_ready.json":
            self.assertEqual(workflow.status, "ready")
            self.assertEqual(workflow.execution_mode, "one_shot")
            self.assertEqual(workflow.latest_version, 21)
            self.assertEqual(workflow.latest_version_status, "published")
            self.assertEqual(workflow.parameter_summary.status, "complete")
            self.assertEqual(len(workflow.available_actions), 3)
            self.assertFalse(workflow.trigger_summary.configured)
        elif fixture_name == "workflow_list_cron_scheduled.json":
            self.assertEqual(workflow.execution_mode, "cron")
            self.assertEqual(workflow.cron_expression, "0 * * * *")
            self.assertTrue(workflow.trigger_summary.configured)
            self.assertFalse(workflow.trigger_summary.enabled)
            self.assertEqual(workflow.parameter_summary.missing_required_fields, 1)
            self.assertEqual(workflow.execution_summary.active_executions, 1)
            self.assertTrue(workflow.execution_summary.active_execution_id)
            self.assertEqual(len(workflow.compute_resource_bindings), 1)
            self.assertTrue(workflow.compute_resource_bindings[0].workflow_level)
        elif fixture_name in {
            "workflow_list_dynamic_service.json",
            "workflow_list_dynamic_service_ready.json",
        }:
            self.assertEqual(workflow.execution_mode, "dynamic_service")
        elif fixture_name == "workflow_list_dynamic_service.json":
            self.assertTrue(workflow.trigger_summary.configured)
            self.assertTrue(workflow.trigger_summary.enabled)
            self.assertEqual(workflow.trigger_summary.service_name, "invoice_lookup")
            self.assertEqual(
                workflow.trigger_summary.input_schema,
                '{"type":"object","required":["invoice_id"]}',
            )
            self.assertEqual(
                workflow.trigger_summary.output_schema,
                '{"type":"object","required":["invoice_total"]}',
            )
        else:
            self._assert_dynamic_service_schemas(workflow.trigger_summary)

    def _assert_dynamic_service_schemas(self, summary):
        self.assertTrue(summary.configured)
        self.assertTrue(summary.enabled)
        self.assertEqual(summary.service_name, "published-service")
        self.assertEqual(
            summary.input_schema,
            '{"type":"object","properties":{"text":{"type":"string"}}}',
        )
        self.assertEqual(
            summary.output_schema,
            '{"type":"object","properties":{"answer":{"type":"string"}}}',
        )

    def _fixture(self, name):
        with (_FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
            return copy.deepcopy(json.load(fixture))


if __name__ == "__main__":
    unittest.main()
