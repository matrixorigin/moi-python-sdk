import unittest
from unittest import mock

import moi_product_sdk as sdk


class WorkflowBatchRetryTest(unittest.TestCase):
    def test_batch_retry_failed_files_uses_typed_contract(self):
        client = sdk.Client("http://example.test/newmoi", sdk.with_api_key("user-key"))
        workflows = client.workflows("ws-1")
        with mock.patch.object(
            workflows,
            "_request",
            return_value={
                "source_dispatch_job_id": "dispatch-source",
                "dispatch_job_id": "dispatch-retry",
                "status": "waiting",
                "accepted_count": 2,
                "replayed": False,
            },
        ) as request:
            response = workflows.batch_retry_failed_files(
                "wf-1", "dispatch-source", ["exec-1", "exec-2"], False, "request-1"
            )

        request.assert_called_once_with(
            "POST",
            "/workflow/v2/workflow-apps/wf-1/executions/batch-retry",
            {
                "source_dispatch_job_id": "dispatch-source",
                "execution_ids": ["exec-1", "exec-2"],
                "request_id": "request-1",
            },
        )
        self.assertEqual(response.dispatch_job_id, "dispatch-retry")
        self.assertEqual(response.accepted_count, 2)


if __name__ == "__main__":
    unittest.main()
