"""Google Embedding ModelClient integration (text-embedding-004)."""

import os
import logging
import asyncio
from typing import Dict, Optional, Any, List

import requests

from adalflow.core.model_client import ModelClient
from adalflow.core.types import (
    ModelType,
    EmbedderOutput,
    Embedding,
    EmbedderOutputType,
)

log = logging.getLogger(__name__)


class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails after retries."""


class GoogleEmbeddingClient(ModelClient):
    """
    Minimal ModelClient to call Google AI Studio Embeddings API.

    - Uses GOOGLE_API_KEY
    - Default model: text-embedding-004
    Docs: https://ai.google.dev/gemini-api/docs/embeddings
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        env_api_key_name: str = "GOOGLE_API_KEY",
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._env_api_key_name = env_api_key_name
        # Google embeddings endpoint is per-model
        # We'll construct full URL from model name at call time
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"

    def _get_api_key(self) -> str:
        api_key = self._api_key or os.getenv(self._env_api_key_name)
        if not api_key:
            raise ValueError(f"Environment variable {self._env_api_key_name} must be set")
        return api_key

    def convert_inputs_to_api_kwargs(
        self,
        input: Any = None,
        model_kwargs: Dict = None,
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict:
        model_kwargs = model_kwargs or {}
        if model_type != ModelType.EMBEDDER:
            raise ValueError(f"model_type {model_type} is not supported")

        # Normalize inputs to a list of strings
        texts: List[str]
        if isinstance(input, list):
            texts = [getattr(x, "text", x) if not isinstance(x, str) else x for x in input]
        elif hasattr(input, "text"):
            texts = [getattr(input, "text")]
        elif isinstance(input, str):
            texts = [input]
        else:
            texts = [str(input)]

        model = model_kwargs.get("model", "text-embedding-004")

        # Google Embeddings expects one input per request. We'll batch in call().
        return {"texts": texts, "model": model}

    def _validate_embedding(self, embedding: List[float], expected_dim: int = 768) -> bool:
        """Validate embedding has correct dimensions."""
        if not embedding:
            raise ValueError("Empty embedding vector")
        if len(embedding) != expected_dim:
            raise ValueError(f"Invalid embedding dimension: {len(embedding)}, expected {expected_dim}")
        return True

    def call(self, api_kwargs: Dict = None, model_type: ModelType = ModelType.UNDEFINED) -> EmbedderOutputType:
        if model_type != ModelType.EMBEDDER:
            raise ValueError(f"model_type {model_type} is not supported")

        api_kwargs = api_kwargs or {}
        texts: List[str] = api_kwargs.get("texts", [])
        model: str = api_kwargs.get("model", "text-embedding-004")

        api_key = self._get_api_key()
        headers = {"Content-Type": "application/json"}

        embeddings: List[Embedding] = []
        any_errors: bool = False
        error_messages: List[str] = []

        # Use batch endpoint for efficiency
        try:
            if len(texts) == 0:
                return EmbedderOutput(data=[], error=None, raw_response=None)

            # Chunk to avoid very large payloads
            chunk_size = 128
            for start in range(0, len(texts), chunk_size):
                chunk = texts[start:start + chunk_size]
                url = f"{self.base_url}/models/{model}:batchEmbedContents?key={api_key}"
                payload = {
                    "model": model,
                    "requests": [
                        {"model": model, "content": {"parts": [{"text": t}]}} for t in chunk
                    ],
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=120)
                if resp.status_code != 200:
                    # Fallback to single-call mode for this chunk
                    log.warning(f"Batch embeddings error ({resp.status_code}), falling back to single requests: {resp.text}")
                    for i, text in enumerate(chunk):
                        single_url = f"{self.base_url}/models/{model}:embedContent?key={api_key}"
                        single_payload = {"model": model, "content": {"parts": [{"text": text}]}}
                        r = requests.post(single_url, json=single_payload, headers=headers, timeout=60)
                        if r.status_code != 200:
                            # Record error and raise exception instead of creating empty vector
                            any_errors = True
                            try:
                                error_msg = r.text[:200]
                            except Exception:
                                error_msg = f"status={r.status_code}"
                            error_messages.append(error_msg)
                            log.error(f"Failed to generate embedding for text at index {start + i}: {error_msg}")
                            raise EmbeddingGenerationError(
                                f"Failed to generate embedding after retries: {error_msg}"
                            )
                        try:
                            d = r.json()
                            vec = d.get("embedding", {}).get("values", [])
                            # Validate embedding dimensions
                            self._validate_embedding(vec)
                        except Exception as e:
                            any_errors = True
                            error_msg = str(e)[:200]
                            error_messages.append(error_msg)
                            log.error(f"Failed to parse embedding for text at index {start + i}: {error_msg}")
                            raise EmbeddingGenerationError(
                                f"Failed to parse or validate embedding: {error_msg}"
                            )
                        embeddings.append(Embedding(embedding=vec, index=start + i))
                else:
                    d = resp.json()
                    # Response shape: { "embeddings": [ { "values": [...] }, ... ] }
                    resp_embs = d.get("embeddings", [])
                    # Ensure we return one embedding per input text in the chunk
                    if len(resp_embs) != len(chunk):
                        any_errors = True
                        log.warning(
                            f"Embeddings count mismatch: received {len(resp_embs)} for {len(chunk)} inputs"
                        )
                    for i in range(len(chunk)):
                        if i < len(resp_embs):
                            vec = resp_embs[i].get("values", [])
                            try:
                                # Validate embedding dimensions
                                self._validate_embedding(vec)
                            except Exception as e:
                                any_errors = True
                                error_msg = f"Invalid embedding at index {start + i}: {str(e)}"
                                error_messages.append(error_msg)
                                log.error(error_msg)
                                raise EmbeddingGenerationError(error_msg)
                        else:
                            # Missing embedding in batch response
                            error_msg = f"Missing embedding for text at index {start + i} in batch response"
                            error_messages.append(error_msg)
                            log.error(error_msg)
                            raise EmbeddingGenerationError(error_msg)
                        embeddings.append(Embedding(embedding=vec, index=start + i))

            error_summary = None
            if any_errors:
                # Summarize errors but still return whatever embeddings we obtained
                unique_msgs = [m for idx, m in enumerate(error_messages) if m not in error_messages[:idx]]
                error_summary = (
                    f"One or more embedding requests failed; partial results returned. "
                    f"Examples: {', '.join(unique_msgs[:3])}"
                )
            return EmbedderOutput(data=embeddings, error=error_summary, raw_response=None)
        except Exception as e:
            log.error(f"Error calling Google embeddings (batch): {e}")
            return EmbedderOutput(data=[], error=str(e), raw_response=None)

    # Avoid pickling issues
    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__.update(state)


