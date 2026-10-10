"""Abstract VLM interface — all model backends must implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class VLMResponse:
    """Response from a vision-language model."""
    answer: str
    raw_output: str = ""
    model_name: str = ""
    model_version: str = ""
    confidence: float | None = None  # Only if derived from model logits
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class VLMBackend(ABC):
    """Abstract interface for vision-language model serving.

    All model backends (vLLM, AI Gateway, demo fallback) implement this.
    Agent logic NEVER depends on which backend is active.
    """

    @abstractmethod
    async def answer_question(
        self,
        image: np.ndarray,
        question: str,
        context: str = "",
    ) -> VLMResponse:
        """Answer a question about an image."""
        ...

    @abstractmethod
    async def generate_caption(
        self,
        image: np.ndarray,
        style: str = "detailed",
    ) -> VLMResponse:
        """Generate a caption for an image."""
        ...

    @abstractmethod
    async def analyze_change(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        question: str = "What changed between these two images?",
    ) -> VLMResponse:
        """Analyze changes between two temporal images."""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """Check if the model backend is healthy and ready."""
        ...

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable name of this backend."""
        ...
