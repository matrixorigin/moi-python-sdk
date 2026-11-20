import unittest

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


class WorkflowMOWLDeployTest(unittest.TestCase):
    def test_deploy_authored_workflow_preserves_native_publication_contract(self):
        calls = []

        class FakeClient:
            def _request(self, method, path, workspace_id, body, require_envelope=False):
                calls.append((method, path, {"workspace_id": workspace_id, "body": body}))
                return {"workflow": {"id": "saved", "source_type": "manual_mowl"}}

        workflow = {"name": "authored", "root": "root", "nets": {"root": {"nodes": {}}}}
        result = sdk_client.WorkflowService(FakeClient(), "workspace").deploy(
            "authored", "", sdk.with_workflow_mowl(workflow),
            sdk.with_workflow_execution_mode("dynamic_service"),
            sdk.with_workflow_dynamic_service(service_name="authored-api", result_mode="oneshot"),
        )
        self.assertEqual(result.workflow.id, "saved")
        self.assertEqual(result.workflow.source_type, "manual_mowl")
        self.assertEqual(calls, [("POST", "/workflow/v2/workflow-deployments", {
            "workspace_id": "workspace", "body": {
                "name": "authored", "source_type": "manual_mowl", "workflow": workflow,
                "execution_mode": "dynamic_service",
                "dynamic_service": {"service_name": "authored-api", "result_mode": "oneshot"},
            },
        })])

    def test_invalid_or_ambiguous_source_is_rejected_before_mutation(self):
        class NeverCalledClient:
            def _request(self, *args, **kwargs):
                raise AssertionError("invalid deployment reached publication owner")

        service = sdk_client.WorkflowService(NeverCalledClient(), "workspace")
        for name, dsl, opts in [
            ("missing", "", ()),
            ("mixed", "workflow: {}", (sdk.with_workflow_mowl({}),)),
            ("null", "", (sdk.with_workflow_mowl(None),)),
            ("array", "", (sdk.with_workflow_mowl([]),)),
            ("candidate", "", (sdk.with_workflow_mowl({}), sdk.with_workflow_source_type("nl2dsl"))),
            ("missing MOWL", "", (sdk.with_workflow_source_type("manual_mowl"),)),
        ]:
            with self.subTest(name=name), self.assertRaises((ValueError, type(sdk_client.ErrDSLYAMLRequired))):
                service.deploy("authored", dsl, *opts)




def _mowl_graph():
    return {
        "name": "probe",
        "root": "root",
        "nets": {
            "root": {
                "nodes": {
                    "__start": {"id": "mowl:start"},
                    "step": {"id": "moi:custom.operator:ws:probe", "version": "v1"},
                    "__end": {"id": "mowl:end"},
                }
            }
        },
    }


class MOWLConvenienceDeployTest(unittest.TestCase):
    def _client(self, calls, data):
        class Client:
            def workflows(self, workspace_id):
                return sdk_client.WorkflowService(self, workspace_id)

            def _request(self, method, path, workspace_id, body, require_envelope=False):
                calls.append((method, path, workspace_id, body))
                return data

        return Client()

    def test_deploy_mowl_sends_manual_mowl_graph(self):
        calls = []
        service = self._client(calls, {"workflow": {"id": "wf-mowl", "source_type": "manual_mowl"}}).workflows("workspace-1")
        envelope = service.deploy_mowl("mowl-wf", _mowl_graph(), sdk_client.with_workflow_description("mowl deploy"))
        self.assertEqual(envelope.workflow.id, "wf-mowl")

        self.assertEqual(len(calls), 1)
        method, path, workspace_id, body = calls[0]
        self.assertEqual((method, path, workspace_id), ("POST", "/workflow/v2/workflow-deployments", "workspace-1"))
        self.assertEqual(body["name"], "mowl-wf")
        self.assertEqual(body["source_type"], "manual_mowl")
        self.assertEqual(body["description"], "mowl deploy")
        self.assertEqual(body["workflow"]["root"], "root")
        self.assertNotIn("dsl_yaml", body)

    def test_deploy_mowl_validates_input(self):
        calls = []
        service = self._client(calls, {}).workflows("workspace-1")
        with self.assertRaises(sdk_client.Error) as raised:
            service.deploy_mowl("", _mowl_graph())
        self.assertEqual(raised.exception.code, "ErrNameRequired")
        with self.assertRaises(ValueError):
            service.deploy_mowl("mowl-wf", {})
        with self.assertRaises(ValueError):
            service.deploy_mowl("mowl-wf", _mowl_graph(), sdk_client.with_workflow_source_type("nl2dsl"))
        self.assertEqual(calls, [])

    def test_create_mowl_workflow_template(self):
        calls = []
        service = self._client(calls, {"id": 11, "definition_format": "mowl", "name": "mowl-tpl"}).workflows("workspace-1")
        template = service.create_mowl_workflow_template("mowl-tpl", _mowl_graph(), sdk_client.with_workflow_template_description("mowl template"))
        self.assertEqual(template.id, 11)

        self.assertEqual(len(calls), 1)
        method, path, workspace_id, body = calls[0]
        self.assertEqual((method, path, workspace_id), ("POST", "/workflow-templates", "workspace-1"))
        self.assertEqual(body["name"], "mowl-tpl")
        self.assertEqual(body["definition_format"], "mowl")
        self.assertEqual(body["description"], "mowl template")
        self.assertEqual(body["workflow"]["root"], "root")
        self.assertNotIn("dsl_yaml", body)

    def test_create_mowl_workflow_template_validates_input(self):
        calls = []
        service = self._client(calls, {}).workflows("workspace-1")
        with self.assertRaises(sdk_client.Error) as raised:
            service.create_mowl_workflow_template("", _mowl_graph())
        self.assertEqual(raised.exception.code, "ErrNameRequired")
        with self.assertRaises(ValueError):
            service.create_mowl_workflow_template("mowl-tpl", {})
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
