"""Agent 3: Sensor Router — Decides Optical, SAR, or both."""

from __future__ import annotations

from ..schemas.agents import ConfidenceLevel, QueryPlan, SensorDecision, SensorDecisionType, TaskType
from ..schemas.imagery import ImageryInput, SensorType
from ..schemas.trace import ExecutionTrace
from .base import AgentBase


class SensorRouterAgent(AgentBase):
    """Agent 3: Choose the right sensor pathway based on query and available imagery.

    Decision logic:
    - If question explicitly mentions SAR/radar → route SAR
    - If flood/water → SAR preferred (cloud-penetrating, water detection)
    - If construction/vegetation → Optical primary, SAR supplementary
    - If both available and question is ambiguous → use both for evidence fusion
    """

    AGENT_ID = 3
    AGENT_NAME = "Sensor Router"

    # Queries where SAR is scientifically valuable
    SAR_PREFERRED_TASKS = {"flood", "water", "moisture", "inundation", "wet"}
    OPTICAL_PREFERRED_TASKS = {"vegetation", "construction", "building", "urban", "ndvi", "crop"}

    async def route(
        self,
        plan: QueryPlan,
        imagery: list[ImageryInput],
        trace: ExecutionTrace,
    ) -> SensorDecision:
        """Decide sensor routing."""
        start = self._trace_start(trace, "Determining sensor pathway")

        # Check what's available
        has_optical = any(i.metadata.sensor_type == SensorType.OPTICAL for i in imagery)
        has_sar = any(i.metadata.sensor_type == SensorType.SAR for i in imagery)

        # If only one sensor available, use it
        if has_optical and not has_sar:
            decision = SensorDecisionType.OPTICAL_ONLY
            reason = "Only optical imagery available."
            confidence = ConfidenceLevel.HIGH
        elif has_sar and not has_optical:
            decision = SensorDecisionType.SAR_ONLY
            reason = "Only SAR imagery available."
            confidence = ConfidenceLevel.HIGH
        elif has_optical and has_sar:
            decision, reason, confidence = self._decide_multi_sensor(plan)
        else:
            # No recognized sensor — try as optical
            decision = SensorDecisionType.OPTICAL_ONLY
            reason = "Sensor type not recognized. Defaulting to optical processing."
            confidence = ConfidenceLevel.LOW
            self._trace_warning(trace, reason)

        result = SensorDecision(
            decision=decision,
            reason=reason,
            optical_available=has_optical,
            sar_available=has_sar,
            recommendation_confidence=confidence,
        )

        self._trace_complete(trace, start, f"Sensor decision: {decision.value}", {
            "decision": decision.value,
            "reason": reason,
            "optical_available": has_optical,
            "sar_available": has_sar,
        })

        return result

    def _decide_multi_sensor(
        self, plan: QueryPlan
    ) -> tuple[SensorDecisionType, str, ConfidenceLevel]:
        """Decide when both optical and SAR are available."""
        q = plan.original_question.lower()

        # SAR-preferred scenarios
        if any(kw in q for kw in self.SAR_PREFERRED_TASKS):
            if plan.requires_temporal:
                return (
                    SensorDecisionType.OPTICAL_AND_SAR,
                    "Flood/water analysis benefits from both optical and SAR. "
                    "SAR provides cloud-penetrating evidence of water extent; "
                    "optical provides visual context.",
                    ConfidenceLevel.HIGH,
                )
            return (
                SensorDecisionType.SAR_ONLY,
                "SAR is the primary sensor for water/moisture detection. "
                "Radar backscatter directly measures surface water.",
                ConfidenceLevel.HIGH,
            )

        # Optical-preferred scenarios
        if any(kw in q for kw in self.OPTICAL_PREFERRED_TASKS):
            return (
                SensorDecisionType.OPTICAL_AND_SAR,
                "Using optical as primary and SAR as supplementary evidence. "
                "Optical shows visible changes; SAR confirms structural changes.",
                ConfidenceLevel.HIGH,
            )

        # Change detection — both sensors are valuable
        if plan.task_type == TaskType.CHANGE_DETECTION:
            return (
                SensorDecisionType.OPTICAL_AND_SAR,
                "Change detection uses both sensors for complementary evidence.",
                ConfidenceLevel.MODERATE,
            )

        # Default to optical with SAR supplement
        return (
            SensorDecisionType.OPTICAL_ONLY,
            "Optical imagery is the primary analysis source for this query.",
            ConfidenceLevel.MODERATE,
        )
