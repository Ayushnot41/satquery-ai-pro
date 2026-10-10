"""Agent-related schemas for the BHUVISION nine-agent system."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of investigation tasks the Query Planner can identify."""
    VQA = "vqa"
    CAPTIONING = "captioning"
    CHANGE_DETECTION = "change_detection"
    VISUAL_GROUNDING = "visual_grounding"
    SAR_ANALYSIS = "sar_analysis"
    MULTI_SENSOR = "multi_sensor"
    UNKNOWN = "unknown"


class SensorDecisionType(str, Enum):
    """Sensor routing decisions."""
    OPTICAL_ONLY = "optical_only"
    SAR_ONLY = "sar_only"
    OPTICAL_AND_SAR = "optical_and_sar"
    NOT_APPLICABLE = "not_applicable"


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


# --- Agent Output Types ---

class QueryPlan(BaseModel):
    """Output of the Query Planner Agent."""
    task_type: TaskType
    requires_temporal: bool = False
    requires_sar: bool = False
    requires_grounding: bool = True
    suggested_tools: list[str] = Field(default_factory=list)
    investigation_summary: str = ""
    original_question: str = ""


class ValidationResult(BaseModel):
    """Output of the Input & Geo Validation Agent."""
    is_valid: bool = True
    file_valid: bool = True
    dimensions_valid: bool = True
    crs_valid: bool = True
    metadata_valid: bool = True
    sensor_compatible: bool = True
    temporal_compatible: bool = True
    coverage_valid: bool = True
    alignment_valid: bool = True
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SensorDecision(BaseModel):
    """Output of the Sensor Router Agent."""
    decision: SensorDecisionType
    reason: str = ""
    optical_available: bool = False
    sar_available: bool = False
    recommendation_confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN


class VQAResult(BaseModel):
    """Output of the Remote-Sensing VQA Agent."""
    answer: str
    raw_model_output: str = ""
    model_name: str = ""
    model_version: str = ""
    logits_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Model confidence from logits, if available"
    )


class ChangeRegion(BaseModel):
    """A detected change region."""
    bbox: list[float] = Field(..., min_length=4, max_length=4, description="[x_min, y_min, x_max, y_max]; see coordinate_space")
    coordinate_space: Literal['pixel', 'normalized'] = 'pixel'
    geo_bbox: list[float] | None = Field(
        None, description="[west, south, east, north] in geographic coords"
    )
    change_type: str = "unknown"
    change_magnitude: float = 0.0
    area_pixels: int = 0
    mask: str | None = Field(None, description="Base64-encoded binary mask")


class ChangeResult(BaseModel):
    """Output of the Bi-Temporal Change Agent."""
    has_change: bool = False
    change_summary: str = ""
    change_regions: list[ChangeRegion] = Field(default_factory=list)
    change_map_path: str | None = None
    method_used: str = ""
    total_changed_pixels: int = 0
    total_pixels: int = 0
    change_percentage: float = 0.0


class GroundingResult(BaseModel):
    """Output of the Visual Grounding Agent."""
    regions: list[ChangeRegion] = Field(default_factory=list)
    overlay_path: str | None = None
    description: str = ""


class EvidenceItem(BaseModel):
    """A single piece of evidence from any agent."""
    source_agent: str
    agent_id: int
    evidence_type: str  # "vqa_answer", "change_map", "grounding", "sar_analysis"
    content: str
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    visual_reference: str | None = None  # Path or URL to visual evidence
    metadata: dict[str, Any] = Field(default_factory=dict)


class FusedEvidence(BaseModel):
    """Output of the Evidence Fusion Agent."""
    primary_answer: str
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    supporting_summary: str = ""
    contradictions: list[str] = Field(default_factory=list)
    evidence_strength: ConfidenceLevel = ConfidenceLevel.UNKNOWN


class ConfidenceReport(BaseModel):
    """Output of the Confidence & Uncertainty Agent."""
    overall_confidence: ConfidenceLevel
    confidence_score: float | None = Field(
        None, ge=0.0, le=1.0,
        description="Numerical score only when derived from measurable evidence"
    )
    explanation: str = ""
    factors: list[str] = Field(default_factory=list, description="What contributed to confidence")
    uncertainties: list[str] = Field(default_factory=list, description="Known uncertainties")
    is_fabricated: bool = Field(
        False,
        description="MUST be False. If we cannot measure confidence, set level to UNKNOWN"
    )


class VisualOverlay(BaseModel):
    """Visual overlay for the frontend."""
    overlay_type: str  # "bbox", "mask", "heatmap", "polygon"
    coordinates: list[list[float]] = Field(default_factory=list)
    coordinate_space: Literal['pixel', 'normalized'] = 'pixel'
    color: str = "#3B82F6"
    opacity: float = 0.4
    label: str = ""
    confidence: float | None = None
