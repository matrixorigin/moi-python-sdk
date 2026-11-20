import json
import unittest

from moi_product_sdk.client import _parse_error, _parse_response
from moi_product_sdk.errors import Error


class ErrorCorrelationTest(unittest.TestCase):
    def test_product_errors_preserve_owner_repair_data(self) -> None:
        feedback = {"diagnostics": [{"field": "name", "reason": "required"}]}
        body = json.dumps({"code": "ErrValidation", "message": "A value is required", "data": feedback}).encode()
        error = _parse_error(422, body, "request-1")
        self.assertEqual((error.code, error.message, error.request_id), ("ErrValidation", "A value is required", "request-1"))
        self.assertEqual(error.data, feedback)
        with self.assertRaises(Error) as raised:
            _parse_response(body, "request-1")
        self.assertEqual(raised.exception.data, feedback)

    def test_product_http_error_with_structured_diagnostic_preserves_public_code(self) -> None:
        for diagnostic in (
            {"domain": "semantic_model", "reason": "TABLE_NOT_IN_MODEL", "metadata": {"table": "payments"}},
            {"code": "diagnostic", "message": "not the public message"},
        ):
            with self.subTest(diagnostic=diagnostic):
                body = {"code": "ErrParamInvalid", "msg": "Table is not in the model", "error": diagnostic}
                error = _parse_error(400, json.dumps(body).encode(), "request-1")
                self.assertEqual((error.code, error.message, error.status, error.request_id),
                                 ("ErrParamInvalid", "Table is not in the model", 400, "request-1"))

    def test_a2a_http_error_rejects_malformed_protocol(self) -> None:
        valid = {"jsonrpc": "2.0", "id": "x", "error": {"code": -32005, "message": "denied"}}
        malformed = [
            {**valid, "jsonrpc": "1.0"},
            {"jsonrpc": "2.0", "error": valid["error"]},
            *({**valid, "id": value} for value in (True, {}, [])),
            {**valid, "result": {}},
            *({**valid, "error": {"code": code, "message": "denied"}} for code in (None, True, 1.5)),
            {**valid, "error": {"code": -32005, "message": None}},
        ]
        for value in malformed:
            with self.subTest(value=value):
                error = _parse_error(403, json.dumps(value).encode(), "header-request")
                self.assertEqual((error.code, error.status, error.request_id), ("ErrResponseInvalid", 403, "header-request"))

    def test_business_error_uses_header_request_id(self) -> None:
        with self.assertRaises(Error) as raised:
            _parse_response(
                b'{"code":"ErrConflict","msg":"name already exists","details":{"request_id":"body-id"}}',
                "header-id",
            )

        self.assertEqual("header-id", raised.exception.request_id)

    def test_http_error_uses_header_request_id(self) -> None:
        error = _parse_error(409, b'{"code":"ErrConflict","msg":"name already exists"}', "header-id")

        self.assertEqual("header-id", error.request_id)

    def test_legacy_error_code_envelope_is_preserved(self) -> None:
        error = _parse_error(403, b'{"error_code":"runtime_artifact_upload_denied"}', "header-id")

        self.assertEqual("runtime_artifact_upload_denied", error.code)
        self.assertEqual("header-id", error.request_id)

    def test_body_request_id_is_not_a_transport_fallback(self) -> None:
        with self.assertRaises(Error) as raised:
            _parse_response(
                b'{"code":"ErrConflict","msg":"name already exists","details":{"request_id":"body-id"}}'
            )

        self.assertEqual("", raised.exception.request_id)

    def test_invalid_required_envelope_uses_header_request_id(self) -> None:
        with self.assertRaises(Error) as raised:
            _parse_response(b'{"unexpected":"response"}', "header-id", require_envelope=True)

        self.assertEqual("ErrResponseInvalid", raised.exception.code)
        self.assertEqual("header-id", raised.exception.request_id)


if __name__ == "__main__":
    unittest.main()
