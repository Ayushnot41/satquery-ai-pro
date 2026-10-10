"""Agent 2: Input & Geo Validation — Validates imagery before analysis."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..schemas.agents import ValidationResult
from ..schemas.imagery import GeoMetadata, ImageryInput, SensorType
from ..schemas.trace import ExecutionTrace
from .base import AgentBase


class InputValidationAgent(AgentBase):
    """Agent 2: Validate files, dimensions, metadata, CRS, and sensor compatibility.

    This agent runs BEFORE any model inference to catch issues early.
    It does not use any AI model — pure deterministic validation.
    """

    AGENT_ID = 2
    AGENT_NAME = "Input & Geo Validation"

    # Accepted CRS patterns
    ACCEPTED_CRS = {"EPSG:4326", "EPSG:32632", "EPSG:32633", "EPSG:32634", "EPSG:32635"}
    MIN_DIMENSION = 32
    MAX_DIMENSION = 10000

    async def validate(
        self,
        imagery: list[ImageryInput],
        trace: ExecutionTrace,
    ) -> ValidationResult:
        """Validate all input imagery."""
        start = self._trace_start(trace, f"Validating {len(imagery)} image(s)")

        result = ValidationResult()
        issues: list[str] = []
        warnings: list[str] = []

        for img in imagery:
            # File existence
            if not Path(img.path).exists():
                issues.append(f"File not found: {img.metadata.filename}")
                result.file_valid = False
                continue

            geo = img.metadata.geo

            # Dimensions
            if geo.width < self.MIN_DIMENSION or geo.height < self.MIN_DIMENSION:
                issues.append(
                    f"{img.metadata.filename}: Image too small "
                    f"({geo.width}x{geo.height}, min {self.MIN_DIMENSION})"
                )
                result.dimensions_valid = False
            elif geo.width > self.MAX_DIMENSION or geo.height > self.MAX_DIMENSION:
                warnings.append(
                    f"{img.metadata.filename}: Image very large "
                    f"({geo.width}x{geo.height}), processing may be slow"
                )

            # CRS
            if geo.crs and geo.crs not in self.ACCEPTED_CRS:
                warnings.append(
                    f"{img.metadata.filename}: Non-standard CRS {geo.crs}, "
                    f"reprojection may be needed"
                )

            # Sensor type
            if img.metadata.sensor_type == SensorType.UNKNOWN:
                warnings.append(
                    f"{img.metadata.filename}: Sensor type unknown, "
                    f"defaulting to optical processing"
                )

        # Temporal pair validation
        temporal_imgs = [i for i in imagery if i.role in ("before", "after")]
        if len(temporal_imgs) == 2:
            before = next((i for i in temporal_imgs if i.role == "before"), None)
            after = next((i for i in temporal_imgs if i.role == "after"), None)
            if before and after:
                self._validate_temporal_pair(before, after, issues, warnings)

        result.issues = issues
        result.warnings = warnings
        result.is_valid = len(issues) == 0

        self._trace_complete(trace, start, (
            f"Validation {'passed' if result.is_valid else 'FAILED'}: "
            f"{len(issues)} issue(s), {len(warnings)} warning(s)"
        ), {
            "is_valid": result.is_valid,
            "issues": issues,
            "warnings": warnings,
        })

        return result

    def _validate_temporal_pair(
        self,
        before: ImageryInput,
        after: ImageryInput,
        issues: list[str],
        warnings: list[str],
    ) -> None:
        """Validate a before/after temporal pair."""
        b_geo = before.metadata.geo
        a_geo = after.metadata.geo

        # CRS alignment
        if b_geo.crs and a_geo.crs and b_geo.crs != a_geo.crs:
            issues.append(
                f"CRS mismatch: {before.metadata.filename} ({b_geo.crs}) vs "
                f"{after.metadata.filename} ({a_geo.crs})"
            )

        # Dimension alignment
        if b_geo.width != a_geo.width or b_geo.height != a_geo.height:
            warnings.append(
                f"Dimension mismatch: {b_geo.width}x{b_geo.height} vs "
                f"{a_geo.width}x{a_geo.height}. Images will be resampled."
            )

        # Temporal order
        if (before.metadata.acquisition_date and after.metadata.acquisition_date
                and before.metadata.acquisition_date > after.metadata.acquisition_date):
            warnings.append("'Before' image has a later date than 'after' image — swapping.")

        # Sensor compatibility
        if before.metadata.sensor_type != after.metadata.sensor_type:
            warnings.append(
                f"Sensor mismatch: {before.metadata.sensor_type.value} vs "
                f"{after.metadata.sensor_type.value}"
            )
