import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import moi_product_sdk as sdk
from moi_product_sdk.runner import AgentRunner


RUNNER = {
    "id": "runner-id",
    "workspace_id": "workspace-id",
    "user_id": "user-id",
    "name": "local runner",
    "runner_type": "custom",
    "edge_agent_id": "runner-runner-id",
    "connect_cmd": "astra-edge --token signed-token",
    "phase": "ready",
    "token_expires_at": "2026-11-04T01:02:03Z",
    "created_at": "2026-10-04T01:02:03Z",
    "updated_at": "2026-10-04T01:02:04Z",
}


class RunnerContractTest(unittest.TestCase):
    def test_typed_methods_use_source_paths_and_preserve_all_fields(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).runners("workspace-id")
        cases = (
            (lambda: service.create("local runner"), "POST", "/agent-runners/custom", {"name": "local runner"}),
            (lambda: service.get("runner-id"), "GET", "/agent-runners/runner-id", None),
            (lambda: service.refresh("runner-id"), "POST", "/agent-runners/runner-id/refresh-token", None),
        )
        for action, method, path, body in cases:
            with self.subTest(path=path), patch.object(service, "_request", return_value=RUNNER) as request:
                result = action()
                self.assertIsInstance(result, AgentRunner)
                for field, value in RUNNER.items():
                    self.assertEqual(getattr(result, field), value)
                if body is None:
                    request.assert_called_once_with(method, path)
                else:
                    request.assert_called_once_with(method, path, body)
        with patch.object(service, "_request", return_value=[RUNNER]) as request:
            result = service.list()
            self.assertEqual([item.id for item in result], ["runner-id"])
            request.assert_called_once_with("GET", "/agent-runners")
        with patch.object(service, "_request", return_value={}) as request:
            self.assertIsNone(service.delete("runner-id"))
            request.assert_called_once_with("DELETE", "/agent-runners/runner-id")

    def test_strict_response_contract_rejects_unknown_fields_and_wrong_shape(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).runners("workspace-id")
        for action, data in (
            (lambda: service.get("runner-id"), {"id": "r", "token_jti": "private"}),
            (service.list, [{"id": "r", "token_jti": "private"}]),
            (service.list, {"runners": []}),
        ):
            with self.subTest(data=data), patch.object(service, "_request", return_value=data), self.assertRaises(sdk.Error):
                action()

    def test_transport_preserves_auth_workspace_request_id_and_public_error(self):
        for option, header, value in (
            (sdk.with_api_key("user-key"), "X-api-key", "user-key"),
            (sdk.with_token("user-token"), "Authorization", "Bearer user-token"),
        ):
            for status, code in (
                (400, "ErrParamInvalid"),
                (404, "ErrRunnerNotFound"),
                (409, "ErrRunnerNameConflict"),
                (409, "ErrRunnerIamRequestConflict"),
                (503, "ErrRunnerIamUnavailable"),
            ):
                with self.subTest(auth=header, code=code):
                    client = sdk.Client(
                        "http://localhost/newmoi", option,
                        sdk.with_custom_header("X-Request-ID", "request-id"),
                    )
                    failure = urllib.error.HTTPError(
                        "http://localhost/newmoi/agent-runners/custom", status, "failure",
                        {"X-Request-ID": "request-id"},
                        io.BytesIO(json.dumps({"code": code, "msg": "原始本地化错误"}).encode()),
                    )
                    with patch("urllib.request.urlopen", side_effect=failure) as request, self.assertRaises(sdk.Error) as raised:
                        client.runners("workspace-id").create("local runner")
                    sent = request.call_args.args[0]
                    self.assertEqual(sent.full_url, "http://localhost/newmoi/agent-runners/custom")
                    self.assertEqual(sent.get_header(header), value)
                    self.assertEqual(sent.get_header("X-workspace-id"), "workspace-id")
                    self.assertEqual(sent.get_header("X-request-id"), "request-id")
                    self.assertEqual(json.loads(sent.data), {"name": "local runner"})
                    self.assertEqual(
                        (raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id),
                        (status, code, "原始本地化错误", "request-id"),
                    )


if __name__ == "__main__":
    unittest.main()
