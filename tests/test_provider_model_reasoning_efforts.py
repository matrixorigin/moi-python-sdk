import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import moi_product_sdk as sdk

from loopback_http import loopback_proxy_environment


def _envelope(models):
    return json.dumps({"code": "OK", "msg": "OK", "data": {"models": models}}).encode()


CHAT_MODELS = [
    {
        "model": "gpt-6-astra",
        "backend_id": -17,
        "backend_name": "Genesis",
        "model_type": "chat",
        "source": "system",
        "system_default": True,
        "reasoning_efforts": ["low", "high", "max"],
    },
    {
        "model": "plain-chat",
        "backend_id": 12,
        "backend_name": "workspace-llm",
        "model_type": "chat",
        "source": "workspace",
        "system_default": False,
    },
]

EMBEDDING_MODELS = [
    {
        "model": "efficientnet-b3",
        "backend_id": -900002,
        "backend_name": "TaaS Embedding",
        "model_type": "embedding",
        "type": "embedding_multimodal",
        "source": "system",
        "system_default": True,
        "dim": 512,
        "reasoning_efforts": ["low"],
    },
    {
        "model": "legacy-embed",
        "backend_id": 12,
        "backend_name": "workspace-embedding",
        "model_type": "embedding",
        "source": "workspace",
        "system_default": False,
    },
]


class ProviderModelReasoningEffortsTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(loopback_proxy_environment())

    def test_public_list_keeps_declared_reasoning_efforts(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split("?", 1)[0] == "/models":
                    body = _envelope(CHAT_MODELS)
                elif self.path.split("?", 1)[0] == "/embedding/models":
                    body = _envelope(EMBEDDING_MODELS)
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = sdk.Client(f"http://127.0.0.1:{server.server_port}", sdk.with_api_key("user-key"))
            models = client.models("ws-reasoning")
            listed = models.list()
            embedding = models.list_embedding_models()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

        self.assertEqual([model.model for model in listed.models], ["gpt-6-astra", "plain-chat"])
        self.assertEqual(list(listed.models[0].reasoning_efforts), ["low", "high", "max"])
        self.assertEqual(list(listed.models[1].reasoning_efforts), [])
        self.assertEqual(listed.models[0].backend_id, -17)
        self.assertTrue(listed.models[0].system_default)
        self.assertEqual([model.model for model in embedding.models], ["efficientnet-b3", "legacy-embed"])
        self.assertEqual(list(embedding.models[0].reasoning_efforts), ["low"])
        self.assertEqual(embedding.models[0].type, "embedding_multimodal")
        self.assertEqual(embedding.models[0].dim, 512)
        self.assertEqual(list(embedding.models[1].reasoning_efforts), [])


if __name__ == "__main__":
    unittest.main()
