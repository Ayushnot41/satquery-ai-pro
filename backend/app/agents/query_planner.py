"""Agent 1: Query Planner — Understands the user's question and decides the investigation type."""

from __future__ import annotations

import re

from ..schemas.agents import QueryPlan, TaskType
from ..schemas.trace import ExecutionTrace
from .base import AgentBase


# Keyword patterns for task classification
_CHANGE_KEYWORDS = {
    "change", "changed", "differ", "different", "increase", "decrease",
    "expand", "shrink", "growth", "before", "after", "between",
    "temporal", "comparison", "compared", "vs", "versus",
}
_SAR_KEYWORDS = {
    "sar", "radar", "backscatter", "polarization", "sentinel-1",
    "moisture", "flood", "water", "inundation",
}
_GROUNDING_KEYWORDS = {
    "where", "location", "locate", "region", "area", "highlight",
    "show", "identify", "point", "mark",
}
_VQA_KEYWORDS = {
    "what", "how many", "count", "describe", "type", "kind",
    "is there", "does", "are there", "classify",
}


class QueryPlannerAgent(AgentBase):
    """Agent 1: Understand the question and decide the investigation strategy.

    This agent does NOT use any model — it is a deterministic rule-based
    classifier that maps keywords + structure to task types. This ensures
    reproducible, auditable routing with zero latency.
    """

    AGENT_ID = 1
    AGENT_NAME = "Query Planner"

    async def plan(self, question: str, trace: ExecutionTrace) -> QueryPlan:
        """Analyze the question and produce an investigation plan."""
        start = self._trace_start(trace, f"Planning investigation for: {question[:100]}")

        q = question.lower().strip()
        words = set(re.findall(r"\w+", q))

        # Detect task type
        task_type = self._classify_task(q, words)

        # Detect requirements
        requires_temporal = bool(words & _CHANGE_KEYWORDS) or task_type == TaskType.CHANGE_DETECTION
        requires_sar = bool(words & _SAR_KEYWORDS)
        requires_grounding = bool(words & _GROUNDING_KEYWORDS) or task_type == TaskType.CHANGE_DETECTION

        # Build tool list
        tools = self._select_tools(task_type, requires_temporal, requires_sar)

        # Investigation summary
        summary = self._summarize(task_type, requires_temporal, requires_sar, requires_grounding)

        plan = QueryPlan(
            task_type=task_type,
            requires_temporal=requires_temporal,
            requires_sar=requires_sar,
            requires_grounding=requires_grounding,
            suggested_tools=tools,
            investigation_summary=summary,
            original_question=question,
        )

        self._trace_complete(trace, start, f"Investigation type: {task_type.value}", {
            "task_type": task_type.value,
            "temporal": requires_temporal,
            "sar": requires_sar,
            "grounding": requires_grounding,
            "tools": tools,
        })

        return plan

    def _classify_task(self, q: str, words: set[str]) -> TaskType:
        """Classify the question into a task type."""
        # Check for change detection first — highest priority
        change_score = len(words & _CHANGE_KEYWORDS)
        if change_score >= 2 or ("between" in q and ("date" in q or "image" in q)):
            return TaskType.CHANGE_DETECTION

        # SAR-specific analysis
        if len(words & _SAR_KEYWORDS) >= 2:
            return TaskType.SAR_ANALYSIS

        # Visual grounding
        if "where" in words and change_score >= 1:
            return TaskType.CHANGE_DETECTION
        if any(k in q for k in ["where is", "where are", "locate", "find the"]):
            return TaskType.VISUAL_GROUNDING

        # Standard VQA
        if words & _VQA_KEYWORDS:
            return TaskType.VQA

        # Default to VQA
        return TaskType.VQA

    def _select_tools(
        self, task_type: TaskType, temporal: bool, sar: bool
    ) -> list[str]:
        """Select tools needed for this investigation."""
        tools = []
        if task_type in (TaskType.VQA, TaskType.CAPTIONING):
            tools.append("vlm_inference")
        if task_type == TaskType.CHANGE_DETECTION or temporal:
            tools.extend(["change_detection", "temporal_alignment"])
        if task_type == TaskType.VISUAL_GROUNDING:
            tools.append("visual_grounding")
        if sar:
            tools.extend(["sar_preprocessing", "sar_analysis"])
        tools.append("evidence_overlay")
        return tools

    def _summarize(
        self,
        task_type: TaskType,
        temporal: bool,
        sar: bool,
        grounding: bool,
    ) -> str:
        """Generate human-readable investigation summary."""
        parts = [f"This is a {task_type.value.replace('_', ' ')} investigation."]
        if temporal:
            parts.append("It requires comparing imagery from different dates.")
        if sar:
            parts.append("SAR (radar) data may provide additional evidence.")
        if grounding:
            parts.append("The relevant region will be highlighted in the imagery.")
        return " ".join(parts)
