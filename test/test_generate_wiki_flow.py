import types
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_client(monkeypatch):
    # Patch RAG in api.simple_chat to avoid cloning/embedding
    import api.simple_chat as sc

    class FakeRAG:
        def __init__(self, provider="google", model=None, use_s3: bool = False):
            self.provider = provider
            self.model = model

        def prepare_retriever(self, *args, **kwargs):
            return None

        def __call__(self, *args, **kwargs):
            # Return None to skip retrieval path
            return None

    def fake_get_model_config(provider="google", model=None):
        # Minimal model config for Google path
        return {
            "model_client": object,  # unused in this path
            "model_kwargs": {
                "model": "gemini-2.5-flash",
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
            },
        }

    class FakeGenModel:
        def __init__(self, model_name: str, generation_config: dict):
            self.model_name = model_name
            self.generation_config = generation_config

        def generate_content(self, prompt: str, stream: bool = False):
            # Simulate streaming generator yielding chunks with .text
            chunk1 = types.SimpleNamespace(text="TEST_STREAM_")
            chunk2 = types.SimpleNamespace(text="OK")
            return [chunk1, chunk2]

    monkeypatch.setattr(sc, "RAG", FakeRAG, raising=True)
    monkeypatch.setattr(sc, "get_model_config", fake_get_model_config, raising=True)

    # Patch google.generativeai.GenerativeModel used inside api.simple_chat via api.api import
    import api.api as api_main
    import api.simple_chat as sc2
    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FakeGenModel, raising=True)

    return TestClient(api_main.app)


def test_chat_stream_ok(app_client: TestClient):
    payload = {
        "repo_url": "https://codeberg.org/maxcodefaster/teammind",
        "type": "codeberg",
        "messages": [{"role": "user", "content": "Say hello"}],
        "provider": "google",
        "model": "gemini-2.5-flash",
        "language": "en",
    }

    resp = app_client.post("/chat/completions/stream", json=payload)
    assert resp.status_code == 200
    body = resp.text
    assert "TEST_STREAM_" in body and "OK" in body


