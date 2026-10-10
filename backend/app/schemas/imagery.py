"""Imagery-related schemas for upload, validation, and metadata."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    """Type of satellite sensor."""
    OPTICAL = "optical"
    SAR = "sar"
    UNKNOWN = "unknown"


class ImageFormat(str, Enum):
    """Supported image formats."""
    GEOTIFF = "geotiff"
    JP2 = "jp2"
    PNG = "png"
    JPEG = "jpeg"
    SAFE = "safe"  # Sentinel-1 SAFE format
    UNKNOWN = "unknown"


class BandInfo(BaseModel):
    """Information about a raster band."""
    index: int
    name: str | None = None
    dtype: str = "float32"
    nodata: float | None = None
    min_value: float | None = None
    max_value: float | None = None


class GeoMetadata(BaseModel):
    """Geospatial metadata extracted from imagery."""
    crs: str | None = Field(None, description="Coordinate Reference System (e.g., EPSG:4326)")
    bounds: list[float] | None = Field(None, description="[west, south, east, north] in CRS units")
    transform: list[float] | None = Field(None, description="Affine transform coefficients")
    width: int = 0
    height: int = 0
    band_count: int = 0
    bands: list[BandInfo] = Field(default_factory=list)
    resolution: tuple[float, float] | None = Field(None, description="Pixel size (x, y) in CRS units")


class ImageryMetadata(BaseModel):
    """Complete metadata for a satellite image."""
    id: str = Field(..., description="Unique imagery identifier")
    filename: str
    file_size_bytes: int = 0
    format: ImageFormat = ImageFormat.UNKNOWN
    sensor_type: SensorType = SensorType.UNKNOWN
    acquisition_date: datetime | None = None
    satellite: str | None = Field(None, description="e.g., Sentinel-2, Sentinel-1, Landsat-8")
    geo: GeoMetadata = Field(default_factory=GeoMetadata)
    extra: dict[str, Any] = Field(default_factory=dict)


class ImageryInput(BaseModel):
    """Input imagery for an investigation."""
    id: str
    path: str
    metadata: ImageryMetadata
    role: str = Field("primary", description="primary | before | after | sar_complement")


class ImageryUploadResponse(BaseModel):
    """Response after uploading imagery."""
    id: str
    filename: str
    metadata: ImageryMetadata
    preview_url: str | None = None
    warnings: list[str] = Field(default_factory=list)
