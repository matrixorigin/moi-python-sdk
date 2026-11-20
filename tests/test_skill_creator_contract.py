import io
import json
import unittest
import urllib.error
from email.message import Message
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

import moi_product_sdk as sdk


class SkillCreatorContractTest(unittest.TestCase):
    def test_confirmation_state_preserves_false_and_query_identity(self):
        service = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key")).agents("workspace 1")
        for saved, bound in ((False, False), (True, False), (True, True)):
            with self.subTest(saved=saved, bound=bound), patch.object(service, "_request", return_value={"skill_id": "skill-1", "workspace_id": "workspace 1", "agent_id": "agent-1", "saved": saved, "bound": bound}) as request:
                result = service.get_skill_candidate_confirmation("task 1", "call /1", "sha256:a+b")
            method, path = request.call_args.args
            self.assertEqual(method, "GET")
            self.assertEqual(urlsplit(path).path, "/workspaces/workspace%201/agent-runtime-tasks/task%201/skills/confirmation")
            self.assertEqual(parse_qs(urlsplit(path).query), {"call_id": ["call /1"], "source_digest": ["sha256:a+b"]})
            self.assertTrue(result.HasField("saved"))
            self.assertTrue(result.HasField("bound"))
            self.assertEqual((result.skill_id, result.saved, result.bound), ("skill-1", saved, bound))

    def test_confirmation_preserves_explicit_false_and_decodes_result(self):
        client = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key"))
        for bind in (False, True):
            body = {"call_id": "call-1", "source_digest": "digest-1", "bind_current": bind}
            data = {"skill_id": "skill-1", "workspace_id": "workspace 1", "agent_id": "agent-1", "bound": bind}
            with self.subTest(bind=bind), patch("urllib.request.urlopen") as request:
                response = request.return_value.__enter__.return_value
                response.read.return_value = json.dumps({"code": "OK", "data": data}).encode()
                response.headers = Message()
                result = client.agents("workspace 1").confirm_skill_candidate("task 1", sdk.ConfirmSkillCandidateRequest(**body))
            sent = request.call_args.args[0]
            self.assertEqual(sent.method, "POST")
            self.assertEqual(sent.full_url, "http://localhost/newmoi/workspaces/workspace%201/agent-runtime-tasks/task%201/skills/confirm")
            self.assertEqual(json.loads(sent.data), body)
            self.assertIsInstance(result, sdk.ConfirmSkillCandidateResult)
            self.assertEqual((result.skill_id, result.workspace_id, result.agent_id, result.bound), ("skill-1", "workspace 1", "agent-1", bind))

    def test_confirmation_preserves_binding_error(self):
        client = sdk.Client("http://localhost/newmoi", sdk.with_api_key("key"))
        details = {"reason": "SKILL_CREATOR_BINDING_FAILED", "saved_skill_id": "skill-1"}
        headers = Message()
        headers["X-Request-ID"] = "request-1"
        failure = urllib.error.HTTPError("http://localhost/newmoi", 409, "failure", headers, io.BytesIO(json.dumps({"code": "ErrConflict", "msg": "Binding was rejected", "details": details}).encode()))
        with patch("urllib.request.urlopen", side_effect=failure), self.assertRaises(sdk.Error) as raised:
            client.agents("workspace-1").confirm_skill_candidate("task-1", sdk.ConfirmSkillCandidateRequest(call_id="call-1"))
        self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id), (409, "ErrConflict", "Binding was rejected", "request-1"))
        self.assertEqual(raised.exception.details, details)
