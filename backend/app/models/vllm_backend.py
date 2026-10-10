"""vLLM Serving Backend — Connects to local high-throughput vLLM instance.

Implements OpenAI-compatible vision chat completions against `http://localhost:8080/v1`
for sub-100ms continuous batching inference of vision-language models.
"""

from __future__ import annotations

import base64
import io
import time
from typing import Any, Dict, Optional

import httpx
import numpy as np
from PIL import Image

from .base import VLMBackend, VLMResponse
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger("models.vllm")


class VLLMBackend(VLMBackend):
    """High-throughput local vLLM vision-language model serving client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self.base_url = (base_url or settings.vllm_api_url).rstrip("/")
        self.model_name = model_name or settings.vlm_model_name
        self.timeout = timeout_seconds

    @property
    def backend_name(self) -> str:
        return "vllm"

    async def health_check(self) -> dict:
        """Check if local vLLM server is reachable."""
        healthy = await self.is_server_healthy()
        return {
            "status": "healthy" if healthy else "offline",
            "backend": self.backend_name,
            "url": self.base_url,
            "model_name": self.model_name,
        }

    def _encode_image(self, image: np.ndarray) -> str:
        """Encode RGB numpy array to base64 JPEG data URL."""
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)
        elif image.ndim == 3 and image.shape[2] == 1:
            image = np.concatenate([image] * 3, axis=-1)
        elif image.ndim == 3 and image.shape[2] > 3:
            image = image[:, :, :3]

        pil_img = Image.fromarray(image.astype(np.uint8) if image.dtype != np.uint8 else image)
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    async def is_server_healthy(self) -> bool:
        """Check if local vLLM instance responds to /health or /models."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    async def answer_question(
        self,
        image: np.ndarray,
        question: str,
        context: str = "",
    ) -> VLMResponse:
        """Query local vLLM server with vision input."""
        start = time.perf_counter()
        img_b64 = self._encode_image(image)

        prompt_text = f"Context: {context}\nQuestion: {question}" if context else question

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are BHUVISION, an expert ISRO remote sensing geospatial analyst.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": img_b64}},
                    ],
                },
            ],
            "max_tokens": 512,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()

                choice = data["choices"][0]
                answer = choice["message"]["content"]
                usage = data.get("usage", {})
                latency = (time.perf_counter() - start) * 1000.0

                return VLMResponse(
                    answer=answer,
                    raw_output=answer,
                    model_name=data.get("model", self.model_name),
                    model_version="vllm-local-0.6",
                    confidence=None,
                    tokens_used=usage.get("total_tokens", 0),
                    latency_ms=round(latency, 2),
                    metadata={"engine": "vllm", "url": self.base_url},
                )
        except Exception as e:
            logger.warning("vllm_inference_failed")
            raise RuntimeError("The configured vLLM provider did not complete inference") from e

    async def generate_caption(
        self,
        image: np.ndarray,
        style: str = "detailed",
    ) -> VLMResponse:
        """Caption satellite tile via vLLM."""
        return await self.answer_question(image, "Describe the primary features, land-use, and structures in this satellite image.")

    async def analyze_change(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        question: str = "What changed between these two images?",
    ) -> VLMResponse:
        """Bi-temporal change analysis via vLLM."""
        def rgb(image):
            if image.ndim == 2:
                return np.repeat(image[..., None], 3, axis=2)
            if image.shape[2] == 1:
                return np.repeat(image, 3, axis=2)
            return image[..., :3]
        before, after = rgb(image_before), rgb(image_after)
        height = max(before.shape[0], after.shape[0])
        combined = np.zeros((height, before.shape[1] + after.shape[1], 3), dtype=np.uint8)
        combined[:before.shape[0], :before.shape[1]] = before
        combined[:after.shape[0], before.shape[1]:] = after
        return await self.answer_question(combined, question, context="Before image on the left; after image on the right. Compare only visible evidence.")
