import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import moi_product_sdk as sdk


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()
        self.headers = {}
        self.status = 200

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class AIStudioServiceSlotsContractTest(unittest.TestCase):
    def setUp(self):
        self.studio = sdk.Client("http://localhost/newmoi", sdk.with_token("admin-token")).ai_studio()

    def _call(self, payload, action):
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)) as urlopen:
            result = action()
        sent = urlopen.call_args.args[0]
        self.assertEqual(sent.get_header("Authorization"), "Bearer admin-token")
        self.assertIsNone(sent.get_header("X-workspace-id"))
        return result, sent

    def test_reads(self):
        result, sent = self._call({"slots": [{"slot_id": "chat"}]}, self.studio.service_slots)
        self.assertEqual((sent.get_method(), sent.full_url), ("GET", "http://localhost/newmoi/admin/aistudio/service-slots"))
        self.assertEqual(result["slots"][0]["slot_id"], "chat")
        result, sent = self._call({"models": []}, self.studio.service_slot_candidates)
        self.assertEqual((sent.get_method(), sent.full_url), ("GET", "http://localhost/newmoi/admin/aistudio/service-slots/candidates"))
        self.assertEqual(result, {"models": []})
        result, sent = self._call({"logs": []}, lambda: self.studio.service_slot_logs(sdk.with_service_slot_log_slot_id("chat/1"), sdk.with_service_slot_log_page_size(5)))
        self.assertEqual((sent.get_method(), sent.full_url), ("GET", "http://localhost/newmoi/admin/aistudio/service-slots/operation-logs?slot_id=chat%2F1&page_size=5"))
        self.assertEqual(result, {"logs": []})

    def test_chat_model_policy(self):
        payload = {"code": "OK", "data": {"default_model": "second", "models": ["second", "first"]}}
        result, sent = self._call(payload, self.studio.chat_model_policy)
        self.assertEqual((sent.get_method(), sent.full_url), ("GET", "http://localhost/newmoi/aistudio/model-policy"))
        self.assertEqual(result, payload["data"])

    def test_put_body_and_path(self):
        reply = {"slot_id": "chat", "default_model_id": "m1", "model_ids": []}
        result, sent = self._call(reply, lambda: self.studio.put_service_slot("chat/1", sdk.PutAIStudioServiceSlotRequest(default_model_id="m1")))
        self.assertEqual((sent.get_method(), sent.full_url), ("PUT", "http://localhost/newmoi/admin/aistudio/service-slots/chat%2F1"))
        self.assertEqual(json.loads(sent.data), {"default_model_id": "m1", "model_ids": [], "extra_json": ""})
        self.assertEqual(result, reply)
        _, sent = self._call(reply, lambda: self.studio.put_service_slot("chat", sdk.PutAIStudioServiceSlotRequest(slot_id="chat", default_model_id="m1", model_ids=["m1", "m2"], extra_json='{"a":1}')))
        self.assertEqual(json.loads(sent.data), {"slot_id": "chat", "default_model_id": "m1", "model_ids": ["m1", "m2"], "extra_json": '{"a":1}'})

    def test_validation_and_error_envelope(self):
        with self.assertRaises(sdk.Error):
            self.studio.put_service_slot("", sdk.PutAIStudioServiceSlotRequest(default_model_id="m1"))
        with self.assertRaises(sdk.Error) as missing:
            self.studio.put_service_slot("chat", None)
        self.assertEqual(missing.exception.code, "ErrRequestRequired")
        failure = urllib.error.HTTPError(
            "http://localhost/newmoi/admin/aistudio/service-slots/chat", 403, "forbidden",
            {"X-Request-ID": "rid-1"}, io.BytesIO(json.dumps({"code": "ErrForbidden", "msg": "需要 taas:admin"}).encode()),
        )
        with patch("urllib.request.urlopen", side_effect=failure), self.assertRaises(sdk.Error) as raised:
            self.studio.put_service_slot("chat", sdk.PutAIStudioServiceSlotRequest(default_model_id="m1"))
        self.assertEqual((raised.exception.status, raised.exception.code, raised.exception.message, raised.exception.request_id),
                         (403, "ErrForbidden", "需要 taas:admin", "rid-1"))


if __name__ == "__main__":
    unittest.main()
