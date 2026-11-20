import json
from pathlib import Path
import unittest

from moi_product_sdk.client import _parse_error


class SandboxNetworkErrorContractTest(unittest.TestCase):
    def test_errors_match_shared_contract(self):
        cases = json.loads((Path(__file__).resolve().parents[2] / "go-sdk/testdata/sandbox_network_error_contract.json").read_text())
        for case in cases:
            with self.subTest(case=case["name"]):
                if case.get("detail_bytes"):
                    detail = "x" * case["detail_bytes"]
                    case["response"]["detail"] = detail
                    if not case["expected_details"].get("detail_omitted"):
                        case["expected_details"]["detail"] = detail
                failure = _parse_error(case["status"], json.dumps(case["response"]).encode(), "transport-request")
                self.assertEqual((failure.code, failure.status, failure.request_id, failure.details),
                                 (case["expected_code"], case["status"], "transport-request", case["expected_details"]))
                self.assertTrue(failure.message)
                self.assertNotEqual(failure.message, case["response"].get("detail"))
                self.assertNotIn("RAW-SECRET", failure.message)
