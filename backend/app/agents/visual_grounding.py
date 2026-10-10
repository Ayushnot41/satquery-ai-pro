"""Agent 6: Visual Grounding — Highlights the image region supporting the answer."""

from __future__ import annotations

import numpy as np

from ..schemas.agents import ChangeRegion, GroundingResult
from ..schemas.trace import ExecutionTrace
from .base import AgentBase


class VisualGroundingAgent(AgentBase):
    """Agent 6: Identify and highlight the image region supporting the answer.

    Uses change detection regions, VQA attention, or saliency maps
    to produce bounding boxes and overlay masks.
    """

    AGENT_ID = 6
    AGENT_NAME = "Visual Grounding"

    async def ground(
        self,
        image: np.ndarray,
        answer_context: str,
        change_regions: list[ChangeRegion] | None = None,
        trace: ExecutionTrace | None = None,
    ) -> GroundingResult:
        """Generate visual grounding for the investigation answer."""
        if trace is None:
            from ..schemas.trace import ExecutionTrace
            trace = ExecutionTrace(investigation_id="inline")

        start = self._trace_start(trace, "Generating visual evidence grounding")

        regions: list[ChangeRegion] = []

        # If change regions exist, use them directly
        if change_regions:
            regions = change_regions
            description = (
                f"Highlighting {len(regions)} region(s) identified by "
                f"the change detection analysis."
            )
        else:
            # Multi-region saliency grounding: identify prominent spatial clusters
            regions = self._saliency_grounding_regions(image, answer_context)
            if regions:
                description = f"Identified {len(regions)} salient spatial parcel/feature cluster(s) in scene."
            else:
                description = "General scene-wide analysis without single localized hotspot."

        result = GroundingResult(
            regions=regions,
            description=description,
        )

        self._trace_complete(trace, start, f"Grounding: {len(regions)} region(s)", {
            "regions": len(regions),
            "method": "change_regions" if change_regions else "saliency_clustering",
        })

        return result

    def _saliency_grounding_regions(self, image: np.ndarray, context: str = "") -> list[ChangeRegion]:
        """Extract multi-region bounding boxes for key visible spatial clusters."""
        try:
            h, w = image.shape[:2]
            if len(image.shape) == 3:
                gray = 0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]
            else:
                gray = image.astype(np.float32)

            mean_val = np.mean(gray)
            saliency = np.abs(gray - mean_val)
            thresh = np.mean(saliency) + 0.4 * np.std(saliency)
            mask = (saliency > thresh).astype(np.uint8)

            from scipy import ndimage
            labeled, num_features = ndimage.label(mask)
            regions: list[ChangeRegion] = []

            # Saliency indicates contrast, not semantic class or calibrated confidence.
            tag_prefix = "Salient region (unclassified)"

            # Sort components by area descending
            counts = np.bincount(labeled.ravel())
            candidate_ids = np.argsort(counts[1:])[::-1] + 1
            components = [(int(counts[i]), labeled == i) for i in candidate_ids[:5] if counts[i] > 100]

            for idx, (area, comp) in enumerate(components[:5]):
                ys, xs = np.where(comp)
                # Normalized 0.0 to 1.0 bounding box coordinates
                xmin = max(0.0, float(xs.min()) / w)
                ymin = max(0.0, float(ys.min()) / h)
                xmax = min(1.0, float(xs.max() + 1) / w)
                ymax = min(1.0, float(ys.max() + 1) / h)

                regions.append(ChangeRegion(
                    bbox=[round(xmin, 4), round(ymin, 4), round(xmax, 4), round(ymax, 4)],
                    change_type=f"{tag_prefix} {chr(65 + idx)}",
                    coordinate_space="normalized",
                    change_magnitude=round(area / (h * w), 4),
                    area_pixels=area,
                ))

            return regions
        except Exception:
            return []
