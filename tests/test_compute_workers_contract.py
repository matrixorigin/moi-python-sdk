"""Compute workers 数组的 SDK 解码回归，响应由本地 fixture 提供。"""

import io
import json
import unittest
from unittest.mock import patch

import moi_product_sdk as sdk


class Response(io.BytesIO):
    status = 200
    headers = {"X-Request-ID": "workers-contract"}

    def __init__(self, envelope):
        super().__init__(json.dumps(envelope).encode())


class ComputeWorkersContractTest(unittest.TestCase):
    def _workers(self, envelope):
        def send(request, **_):
            self.assertEqual(request.method, "GET")
            self.assertEqual(
                request.full_url,
                "https://backend.invalid/newmoi/compute-resources/compute-1/workers",
            )
            self.assertEqual(request.get_header("X-workspace-id"), "workspace-1")
            return Response(envelope)

        client = sdk.Client(
            "https://backend.invalid/newmoi", sdk.with_api_key("test-key")
        )
        with (
            patch("urllib.request.urlopen", send),
            patch(
                "urllib.request.OpenerDirector.open",
                lambda _, request, **kwargs: send(request, **kwargs),
            ),
        ):
            return client.compute("workspace-1").workers("compute-1")

    def test_empty_and_populated_worker_arrays_decode(self):
        self.assertEqual(self._workers({"code": "OK", "data": []}), [])
        workers = self._workers(
            {
                "code": "OK",
                "data": [
                    {
                        "instance_id": "worker-1",
                        "worker_type": "python",
                        "status": "READY",
                        "py_requirements_sha": "sha-1",
                        "py_requirements_status": "succeeded",
                        "py_requirements_error": "",
                    }
                ],
            }
        )
        self.assertEqual(
            [
                (
                    worker.instance_id,
                    worker.worker_type,
                    worker.status,
                    worker.py_requirements_sha,
                    worker.py_requirements_status,
                    worker.py_requirements_error,
                )
                for worker in workers
            ],
            [("worker-1", "python", "READY", "sha-1", "succeeded", "")],
        )

    def test_malformed_worker_responses_stay_failures(self):
        for envelope in (
            {"code": "OK"},
            {"code": "OK", "data": None},
            {"code": "OK", "data": {}},
            {"code": "OK", "data": "workers"},
            {"code": "OK", "data": ["worker-1"]},
        ):
            with self.subTest(envelope=envelope), self.assertRaises(sdk.Error):
                self._workers(envelope)


if __name__ == "__main__":
    unittest.main()
