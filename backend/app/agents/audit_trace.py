"""Agent 9: Audit & Trace — Creates observable execution records."""

from __future__ import annotations

from datetime import datetime

from ..schemas.trace import ExecutionTrace, TraceEvent, TraceEventType
from .base import AgentBase


class AuditTraceAgent(AgentBase):
    """Agent 9: Create an observable record of the investigation.

    This agent is special — it doesn't produce analytical output.
    Instead, it creates a complete, human-readable audit trail of
    what happened during the investigation.
    """

    AGENT_ID = 9
    AGENT_NAME = "Audit & Trace"

    async def finalize_trace(
        self,
        trace: ExecutionTrace,
    ) -> ExecutionTrace:
        """Finalize and validate the execution trace."""
        start = self._trace_start(trace, "Finalizing execution trace")

        # Complete the trace
        trace.complete()

        # Validate trace integrity
        issues = self._validate_trace(trace)
        if issues:
            for issue in issues:
                self._trace_warning(trace, f"Trace integrity: {issue}")

        self._trace_complete(trace, start, (
            f"Trace finalized: {len(trace.events)} events, "
            f"{len(trace.agents_invoked)} agents, "
            f"{trace.total_duration_ms:.0f}ms total"
        ), {
            "total_events": len(trace.events),
            "agents_invoked": trace.agents_invoked,
            "models_used": trace.models_used,
            "warnings": len(trace.warnings),
            "errors": len(trace.errors),
            "fallbacks": len(trace.fallbacks_used),
        })

        return trace

    def _validate_trace(self, trace: ExecutionTrace) -> list[str]:
        """Validate trace integrity."""
        issues = []

        # Check that all expected agents were invoked
        expected_agents = {
            "Query Planner",
            "Input & Geo Validation",
            "Sensor Router",
        }
        invoked = set(trace.agents_invoked)
        missing = expected_agents - invoked
        if missing:
            issues.append(f"Core agents not invoked: {', '.join(missing)}")

        # Check for orphaned errors
        errors_without_fallback = len(trace.errors) - len(trace.fallbacks_used)
        if errors_without_fallback > 0:
            issues.append(
                f"{errors_without_fallback} error(s) occurred without fallback handling"
            )

        # Check timing consistency
        if trace.total_duration_ms and trace.total_duration_ms < 0:
            issues.append("Negative total duration detected — clock issue")

        return issues

    def generate_human_summary(self, trace: ExecutionTrace) -> str:
        """Generate a human-readable summary of the investigation trace."""
        lines = [
            "## Investigation Trace",
            f"**Duration:** {trace.total_duration_ms:.0f}ms" if trace.total_duration_ms else "",
            f"**Agents Used:** {', '.join(trace.agents_invoked)}",
            f"**Models Used:** {', '.join(trace.models_used) or 'None'}",
        ]

        if trace.warnings:
            lines.append(f"\n**⚠ Warnings ({len(trace.warnings)}):**")
            for w in trace.warnings:
                lines.append(f"- {w}")

        if trace.errors:
            lines.append(f"\n**❌ Errors ({len(trace.errors)}):**")
            for e in trace.errors:
                lines.append(f"- {e}")

        if trace.fallbacks_used:
            lines.append(f"\n**↩ Fallbacks ({len(trace.fallbacks_used)}):**")
            for f in trace.fallbacks_used:
                lines.append(f"- {f}")

        lines.append(f"\n**Total Events:** {len(trace.events)}")

        return "\n".join(line for line in lines if line)
