import unittest
from unittest import mock

import moi_product_sdk as sdk
import moi_product_sdk.client as sdk_client


class WorkflowDispatchContractTest(unittest.TestCase):
    def test_receipt_drives_dispatch_observation(self):
        receipt = sdk_client._workflow_run_envelope({"workflow_run": {
            "execution_id": "dispatch-1", "dispatch_job_id": "dispatch-1",
            "workflow_id": "wf-1", "status": "waiting", "available_actions": [],
        }})
        self.assertEqual(receipt.workflow_run.dispatch_job_id, "dispatch-1")
        service = sdk_client.WorkflowService(mock.Mock(), "ws-1")
        payload = {"dispatch_job": {
            "dispatch_job_id": "dispatch-1", "workflow_id": "wf-1",
            "status": "completed", "total_deliveries": 2,
            "pending_deliveries": 0, "failed_deliveries": 0,
        }}
        with mock.patch.object(service, "_request", return_value=payload) as request:
            result = service.get_dispatch_job("wf-1", receipt.workflow_run.dispatch_job_id)
        request.assert_called_once_with("GET", "/workflow/v2/workflow-apps/wf-1/dispatch-jobs/dispatch-1")
        self.assertIsInstance(result, sdk.WorkflowDispatchJobEnvelope)
        self.assertEqual(result.dispatch_job.dispatch_job_id, "dispatch-1")
        self.assertEqual(result.dispatch_job.workflow_id, "wf-1")
        self.assertEqual(result.dispatch_job.status, "completed")
        self.assertEqual(result.dispatch_job.total_deliveries, 2)
        self.assertEqual(result.dispatch_job.pending_deliveries, 0)
        self.assertEqual(result.dispatch_job.failed_deliveries, 0)

    def test_dispatch_observation_preserves_owner_errors(self):
        service = sdk_client.WorkflowService(mock.Mock(), "ws-1")
        failure = RuntimeError("owner unavailable")
        with mock.patch.object(service, "_request", side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, "owner unavailable"):
                service.get_dispatch_job("wf-1", "dispatch-1")
