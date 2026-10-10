"""Base agent class — all nine BHUVISION agents inherit from this."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from ..core.logging import get_logger
from ..schemas.trace import ExecutionTrace, TraceEvent, TraceEventType


class AgentBase(ABC):
    """Base class for all BHUVISION agentic components.

    Each agent:
    - Has a unique ID (1-9) and name
    - Produces typed outputs
    - Records events to the execution trace
    - Handles errors gracefully
    """

    AGENT_ID: int = 0
    AGENT_NAME: str = "BaseAgent"

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.AGENT_NAME}")

    def _trace_start(self, trace: ExecutionTrace, message: str = "") -> float:
        """Record agent start in the trace and return start time."""
        trace.add_event(TraceEvent(
            event_type=TraceEventType.AGENT_START,
            agent_name=self.AGENT_NAME,
            agent_id=self.AGENT_ID,
            message=message or f"{self.AGENT_NAME} started",
        ))
        return time.time()

    def _trace_complete(
        self,
        trace: ExecutionTrace,
        start_time: float,
        message: str = "",
        details: dict[str, Any] | None = None,
        model_used: str | None = None,
    ) -> None:
        """Record agent completion in the trace."""
        duration_ms = (time.time() - start_time) * 1000
        trace.add_event(TraceEvent(
            event_type=TraceEventType.AGENT_COMPLETE,
            agent_name=self.AGENT_NAME,
            agent_id=self.AGENT_ID,
            message=message or f"{self.AGENT_NAME} completed",
            details=details or {},
            duration_ms=duration_ms,
            model_used=model_used,
        ))

    def _trace_error(
        self,
        trace: ExecutionTrace,
        error: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record agent error in the trace."""
        trace.add_event(TraceEvent(
            event_type=TraceEventType.AGENT_ERROR,
            agent_name=self.AGENT_NAME,
            agent_id=self.AGENT_ID,
            message=error,
            details=details or {},
        ))

    def _trace_warning(self, trace: ExecutionTrace, warning: str) -> None:
        """Record a warning in the trace."""
        trace.add_event(TraceEvent(
            event_type=TraceEventType.WARNING,
            agent_name=self.AGENT_NAME,
            agent_id=self.AGENT_ID,
            message=warning,
        ))

    def _trace_fallback(self, trace: ExecutionTrace, reason: str) -> None:
        """Record that a fallback was used."""
        trace.add_event(TraceEvent(
            event_type=TraceEventType.FALLBACK_USED,
            agent_name=self.AGENT_NAME,
            agent_id=self.AGENT_ID,
            message=reason,
        ))
