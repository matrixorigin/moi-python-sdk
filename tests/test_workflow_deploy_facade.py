import unittest

import moi_product_sdk.client as sdk

from test_workflow_candidate_deploy import _accepted_candidate


class WorkflowDeployFacadeTest(unittest.TestCase):
    def test_deployment_identity(self):
        for candidate in (False, True):
            for name, supplied_id, response_id, code, status in (
                ("create", "", "server-created", "", 0),
                ("create_without_argument", None, "server-created", "", 0),
                ("update", "existing", "existing", "", 0),
                ("option_selects_existing", "original", "selected", "", 0),
                ("missing_target", "missing", "", "ErrWorkflowDeploymentTargetNotFound", 404),
                ("missing_response_id", "existing", "", "ErrResponseInvalid", 0),
            ):
                with self.subTest(candidate=candidate, scenario=name):
                    calls = []

                    class Client:
                        def workflows(self, workspace_id):
                            return sdk.WorkflowService(self, workspace_id)

                        def _request(self, method, path, workspace_id, body, require_envelope=False):
                            calls.append((method, path, workspace_id, body))
                            if status:
                                raise sdk.Error(code, "Workflow does not exist", status=status, details={"workflow_id": supplied_id})
                            return {"workflow": {"id": response_id}}

                    workspace = sdk.WorkspaceHandle(Client(), "workspace-1")
                    opts = (sdk.with_workflow_id("selected"),) if name == "option_selects_existing" else ()

                    def deploy():
                        if supplied_id is None:
                            if candidate:
                                return workspace.deploy_workflow_candidate("workflow", _accepted_candidate())
                            return workspace.deploy_workflow("workflow", "workflow:\n  name: workflow")
                        if candidate:
                            return workspace.deploy_workflow_candidate("workflow", _accepted_candidate(), supplied_id, *opts)
                        return workspace.deploy_workflow("workflow", "workflow:\n  name: workflow", supplied_id, *opts)

                    if code:
                        with self.assertRaises(sdk.Error) as raised:
                            deploy()
                        self.assertEqual(raised.exception.code, code)
                        if code == "ErrResponseInvalid":
                            self.assertEqual(raised.exception.details, {"kind": "workflow"})
                            self.assertEqual(raised.exception.request_id, "")
                        if status:
                            self.assertEqual(raised.exception.status, status)
                            self.assertEqual(raised.exception.message, "Workflow does not exist")
                            self.assertEqual(raised.exception.details, {"workflow_id": supplied_id})
                    else:
                        handle, result = deploy()
                        self.assertEqual(handle.id, response_id)
                        self.assertEqual(result.workflow.id, handle.id)
                        self.assertEqual(handle.info().workflow.id, handle.id)
                        self.assertEqual(calls[-1][1], "/workflow/v2/workflow-apps/" + response_id)

                    method, path, workspace_id, body = calls[0]
                    self.assertEqual((method, path, workspace_id), ("POST", "/workflow/v2/workflow-deployments", "workspace-1"))
                    if supplied_id:
                        self.assertEqual(body["workflow_id"], "selected" if opts else supplied_id)
                    else:
                        self.assertNotIn("workflow_id", body)


if __name__ == "__main__":
    unittest.main()
