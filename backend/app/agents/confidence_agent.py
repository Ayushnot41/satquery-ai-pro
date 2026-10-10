"""Agent 8: Confidence & Uncertainty — Estimates reliability from measurable evidence."""

from __future__ import annotations

from ..schemas.agents import ConfidenceLevel, ConfidenceReport, FusedEvidence
from ..schemas.trace import ExecutionTrace
from .base import AgentBase


class ConfidenceAgent(AgentBase):
    """Agent 8: Estimate reliability from measurable evidence and clearly state uncertainty.

    CRITICAL RULES:
    - NEVER fabricate confidence scores
    - Confidence MUST be derived from measurable evidence
    - When evidence is insufficient, report UNKNOWN — do not guess
    - Always explain what factors contribute to confidence
    """

    AGENT_ID = 8
    AGENT_NAME = "Confidence & Uncertainty"

    async def assess(
        self,
        evidence: FusedEvidence,
        trace: ExecutionTrace | None = None,
    ) -> ConfidenceReport:
        """Assess confidence based on available evidence."""
        if trace is None:
            from ..schemas.trace import ExecutionTrace
            trace = ExecutionTrace(investigation_id="inline")

        start = self._trace_start(trace, "Assessing confidence and uncertainty")

        factors: list[str] = []
        uncertainties: list[str] = []
        score: float | None = None

        # Factor 1: Number of evidence sources
        n_evidence = len(evidence.evidence_items)
        if n_evidence >= 3:
            factors.append(f"Multiple evidence sources ({n_evidence}) provide corroboration")
        elif n_evidence == 2:
            factors.append("Two independent evidence sources available")
        elif n_evidence == 1:
            uncertainties.append("Only one evidence source — no independent corroboration")
        else:
            uncertainties.append("No evidence sources available")

        # Factor 2: Contradictions
        if evidence.contradictions:
            uncertainties.append(
                f"Evidence contradictions detected: {'; '.join(evidence.contradictions)}"
            )

        # Factor 3: Model confidence (only if available from logits)
        model_confidences = [
            item.confidence for item in evidence.evidence_items
            if item.confidence is not None
        ]
        if model_confidences:
            avg_model_conf = sum(model_confidences) / len(model_confidences)
            factors.append(f"Model logits confidence: {avg_model_conf:.2f}")
            score = avg_model_conf  # Use actual model confidence
        else:
            uncertainties.append(
                "No model logits confidence available — confidence is qualitative only"
            )

        # Factor 4: Demo mode
        demo_items = [
            i for i in evidence.evidence_items
            if i.metadata.get("is_demo", False)
        ]
        if demo_items:
            uncertainties.append("Results include demo/cached data, not live model inference")

        # Factor 5: Change detection specifics
        change_items = [
            i for i in evidence.evidence_items
            if i.evidence_type == "change_map"
        ]
        if change_items:
            for ci in change_items:
                pct = ci.metadata.get("change_percentage", 0)
                if pct > 5:
                    factors.append(f"Significant change detected ({pct}% area)")
                elif pct > 0:
                    uncertainties.append(f"Small change area ({pct}%) may be noise")

        # Determine overall level
        level = self._determine_level(factors, uncertainties, evidence.contradictions)

        # Generate explanation
        explanation = self._generate_explanation(level, factors, uncertainties)

        result = ConfidenceReport(
            overall_confidence=level,
            confidence_score=score,
            explanation=explanation,
            factors=factors,
            uncertainties=uncertainties,
            is_fabricated=False,  # ALWAYS False
        )

        self._trace_complete(trace, start, f"Confidence: {level.value}", {
            "level": level.value,
            "score": score,
            "factors_count": len(factors),
            "uncertainties_count": len(uncertainties),
        })

        return result

    def _determine_level(
        self,
        factors: list[str],
        uncertainties: list[str],
        contradictions: list[str],
    ) -> ConfidenceLevel:
        """Determine confidence level from evidence."""
        if not factors and uncertainties:
            return ConfidenceLevel.UNKNOWN

        if contradictions:
            return ConfidenceLevel.LOW

        if len(factors) >= 3 and len(uncertainties) <= 1:
            return ConfidenceLevel.HIGH

        if len(factors) >= 2:
            return ConfidenceLevel.MODERATE

        if len(uncertainties) > len(factors):
            return ConfidenceLevel.LOW

        return ConfidenceLevel.MODERATE

    def _generate_explanation(
        self,
        level: ConfidenceLevel,
        factors: list[str],
        uncertainties: list[str],
    ) -> str:
        """Generate human-readable confidence explanation."""
        parts = [f"Overall confidence: {level.value.upper()}."]

        if factors:
            parts.append(f"Supporting factors: {'; '.join(factors)}.")

        if uncertainties:
            parts.append(f"Uncertainties: {'; '.join(uncertainties)}.")

        return " ".join(parts)
