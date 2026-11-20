import unittest

from google.protobuf import json_format

from moi_product_sdk._proto.product import compute_pb2


class ComputeAllowedActionsContractTest(unittest.TestCase):
    def test_workspace_compute_resource_decodes_allowed_actions(self):
        resource = json_format.ParseDict(
            {
                "id": "compute-1",
                "allowed_actions": [
                    "compute_resource.update",
                    "compute_resource.delete",
                ],
            },
            compute_pb2.ComputeResource(),
        )

        self.assertEqual(
            list(resource.allowed_actions),
            ["compute_resource.update", "compute_resource.delete"],
        )

    def test_admin_compute_resource_does_not_expose_workspace_actions(self):
        fields = compute_pb2.AdminComputeResource.DESCRIPTOR.fields_by_name
        self.assertNotIn("allowed_actions", fields)


if __name__ == "__main__":
    unittest.main()
