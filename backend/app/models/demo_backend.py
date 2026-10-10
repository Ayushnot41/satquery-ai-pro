"""Deterministic demo backend — pre-computed responses for curated scenarios.

This backend is used when:
- GPU/model serving is unavailable
- DEMO_MODE=true
- Live inference fails and we need graceful fallback

IMPORTANT: Demo outputs are ALWAYS labeled as demo data, never as live inference.
"""

from __future__ import annotations

import time

import numpy as np

from .base import VLMBackend, VLMResponse

# Pre-computed demo responses keyed by scenario hints
DEMO_RESPONSES: dict[str, dict] = {
    "construction": {
        "vqa": (
            "The image shows significant construction activity. New building structures "
            "are visible in the southeastern quadrant of the image, with cleared land "
            "and foundation work evident. The surrounding area shows mixed urban and "
            "agricultural land use."
        ),
        "change": (
            "Construction has increased in the region. New structures are visible "
            "in the southeastern portion of the image. Approximately 12% of the "
            "analyzed area shows new construction activity compared to the earlier image."
        ),
        "caption": (
            "Satellite view of an urban-rural transition zone showing recent construction "
            "activity. New buildings and cleared plots are visible alongside existing "
            "residential areas and agricultural fields."
        ),
    },
    "flood": {
        "vqa": (
            "The image shows flooding in the low-lying areas near the river. "
            "Water has expanded beyond the normal riverbed into adjacent agricultural "
            "fields and settlement areas. SAR imagery confirms water presence in "
            "areas that appear ambiguous in optical data."
        ),
        "change": (
            "Flooding has expanded significantly. The water body has increased by "
            "approximately 340% compared to the pre-flood image. Inundation is "
            "primarily visible in the northern and eastern flood plains."
        ),
        "caption": (
            "Satellite image showing flood conditions with expanded water coverage "
            "along a river system. Agricultural and residential areas are partially "
            "inundated."
        ),
    },
    "vegetation": {
        "vqa": (
            "The image shows changes in vegetation cover. Dense vegetation has decreased "
            "in the western portion, possibly due to deforestation or seasonal changes. "
            "Agricultural fields show varying crop growth stages."
        ),
        "change": (
            "Vegetation change detected: NDVI values have decreased by an average of "
            "0.15 in the western region, indicating reduced vegetation density. "
            "This could indicate deforestation, harvesting, or drought stress."
        ),
        "caption": (
            "Satellite view of a mixed landscape showing varying vegetation density, "
            "agricultural parcels, and areas of reduced vegetation cover."
        ),
    },
    "default": {
        "vqa": (
            "The satellite image shows a mixed land-use area with visible structures, "
            "vegetation, and open terrain. More specific analysis would require "
            "additional context about the area of interest."
        ),
        "change": (
            "Changes are detected between the two time periods. The most significant "
            "changes appear in the central portion of the image."
        ),
        "caption": (
            "Satellite image of a geographic area showing mixed land cover including "
            "built-up areas, vegetation, and open terrain."
        ),
    },
}


class DemoBackend(VLMBackend):
    """Deterministic demo backend with pre-computed responses."""

    def _detect_scenario(self, question: str) -> str:
        """Detect which demo scenario matches the question."""
        q = question.lower()
        if any(w in q for w in ["construct", "building", "built", "urban"]):
            return "construction"
        if any(w in q for w in ["flood", "water", "inundat"]):
            return "flood"
        if any(w in q for w in ["vegetat", "ndvi", "green", "forest", "crop"]):
            return "vegetation"
        return "default"

    async def answer_question(
        self,
        image: np.ndarray,
        question: str,
        context: str = "",
    ) -> VLMResponse:
        scenario = self._detect_scenario(question)
        start = time.time()
        answer = DEMO_RESPONSES[scenario]["vqa"]

        return VLMResponse(
            answer=f"[DEMO MODE] {answer}",
            raw_output=answer,
            model_name="demo-fallback",
            model_version="deterministic-v1",
            confidence=None,  # Never fabricate confidence in demo mode
            latency_ms=(time.time() - start) * 1000,
            metadata={"scenario": scenario, "is_demo": True},
        )

    async def generate_caption(
        self,
        image: np.ndarray,
        style: str = "detailed",
    ) -> VLMResponse:
        start = time.time()
        caption = DEMO_RESPONSES["default"]["caption"]
        return VLMResponse(
            answer=f"[DEMO MODE] {caption}",
            raw_output=caption,
            model_name="demo-fallback",
            model_version="deterministic-v1",
            latency_ms=(time.time() - start) * 1000,
            metadata={"is_demo": True},
        )

    async def analyze_change(
        self,
        image_before: np.ndarray,
        image_after: np.ndarray,
        question: str = "What changed between these two images?",
    ) -> VLMResponse:
        scenario = self._detect_scenario(question)
        start = time.time()
        answer = DEMO_RESPONSES[scenario]["change"]

        return VLMResponse(
            answer=f"[DEMO MODE] {answer}",
            raw_output=answer,
            model_name="demo-fallback",
            model_version="deterministic-v1",
            latency_ms=(time.time() - start) * 1000,
            metadata={"scenario": scenario, "is_demo": True},
        )

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "backend": "demo",
            "note": "Running in deterministic demo mode. Outputs are pre-computed.",
        }

    @property
    def backend_name(self) -> str:
        return "Demo Fallback (Deterministic)"
