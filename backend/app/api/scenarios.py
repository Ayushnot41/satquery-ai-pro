"""Curated demo scenarios for BHUVISION hackathon presentation."""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas.investigation import DemoScenario

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

DEMO_SCENARIOS: list[DemoScenario] = [
    DemoScenario(
        id="scenario-construction-01",
        name="Urban Construction Expansion",
        description="Bi-temporal analysis of new commercial and residential developments near an urban periphery.",
        question="Where has construction increased between these two dates?",
        imagery_ids=["demo-construction-before", "demo-construction-after"],
        expected_task_type="change_detection",
        category="construction",
    ),
    DemoScenario(
        id="scenario-flood-01",
        name="Monsoon Riverine Inundation (SAR + Optical)",
        description="Multi-sensor flood boundary delineation combining Sentinel-1 radar backscatter and Sentinel-2 optical imagery.",
        question="Where did flooding expand?",
        imagery_ids=["demo-flood-pre-optical", "demo-flood-post-sar"],
        expected_task_type="change_detection",
        category="flood",
    ),
    DemoScenario(
        id="scenario-vegetation-01",
        name="Forest Canopy & Agricultural Shift",
        description="Assessment of seasonal vegetation loss and canopy depletion in protected forest buffers.",
        question="Where has vegetation changed?",
        imagery_ids=["demo-veg-t1", "demo-veg-t2"],
        expected_task_type="change_detection",
        category="vegetation",
    ),
]


@router.get("", response_model=list[DemoScenario])
async def list_scenarios() -> list[DemoScenario]:
    """List all available curated demo scenarios."""
    return DEMO_SCENARIOS


@router.get("/{scenario_id}", response_model=DemoScenario | None)
async def get_scenario(scenario_id: str) -> DemoScenario | None:
    """Get scenario details by ID."""
    return next((s for s in DEMO_SCENARIOS if s.id == scenario_id), None)
