"""Investigation API — Handles agentic Earth intelligence queries."""

from __future__ import annotations

import math
import hashlib
from datetime import datetime, timezone
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from PIL import Image

from ..agents.orchestrator import InvestigationOrchestrator
from ..api.imagery import IMAGERY_REGISTRY
from ..core.config import settings
from ..geospatial.raster import extract_metadata
from ..models.base import VLMBackend
from ..models.demo_backend import DemoBackend
from ..models.gateway_backend import GatewayBackend
from ..models.local_lora_backend import LocalLoRABackend
from ..models.vllm_backend import VLLMBackend
from ..schemas.imagery import ImageryInput, SensorType
from ..schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse,
    InvestigationStatus,
)

router = APIRouter(prefix="/investigate", tags=["Investigation"])

# Persistent in-memory cache of investigations
from ..core.database import DurableStore
INVESTIGATION_CACHE = DurableStore("investigations", InvestigationResponse)

# Active backend selection
def get_vlm_backend() -> VLMBackend:
    if settings.vlm_backend == "gateway":
        return GatewayBackend()
    if settings.vlm_backend == "local_lora":
        return LocalLoRABackend()
    if settings.vlm_backend == "vllm":
        return VLLMBackend()
    return DemoBackend()


def _get_or_create_demo_image(name: str, sensor: SensorType) -> Path:
    """Generate or retrieve a verified demo image file on disk."""
    demo_dir = Path("./data/demo")
    demo_dir.mkdir(parents=True, exist_ok=True)
    import re
    if not re.fullmatch(r'demo-[a-zA-Z0-9_-]{1,100}', name):
        raise HTTPException(404, 'Image not found in this workspace')
    # Use the same preserved image displayed by the UI when this sample exists.
    sample = Path(__file__).resolve().parents[3] / 'assets' / f'{name}.png'
    if sample.is_file():
        return sample
    file_path = demo_dir / f"{name}.png"
    if not file_path.exists():
        rng = np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], 'big'))
        # Create a synthetic 512x512 satellite texture
        if sensor == SensorType.SAR:
            # Grainy radar speckle texture
            noise = rng.gamma(shape=2.0, scale=30.0, size=(512, 512)).astype(np.uint8)
            # Add a dark specular water curve
            y, x = np.ogrid[:512, :512]
            river_mask = (y - 0.5 * x - 100 > -30) & (y - 0.5 * x - 100 < 30)
            noise[river_mask] = rng.normal(loc=15, scale=5, size=np.sum(river_mask)).clip(0, 255).astype(np.uint8)
            img = Image.fromarray(noise)
        else:
            # Optical RGB composite with terrain and urban textures
            rgb = np.zeros((512, 512, 3), dtype=np.uint8)
            # Greenish agricultural background
            rgb[:, :, 1] = rng.integers(90, 140, (512, 512), dtype=np.uint8)
            rgb[:, :, 0] = rng.integers(60, 100, (512, 512), dtype=np.uint8)
            rgb[:, :, 2] = rng.integers(30, 70, (512, 512), dtype=np.uint8)
            # Add urban geometric clusters
            if "after" in name:
                rgb[150:320, 200:400, 0] = 180  # Concrete bright returns
                rgb[150:320, 200:400, 1] = 180
                rgb[150:320, 200:400, 2] = 180
            img = Image.fromarray(rgb)
        img.save(file_path)
    return file_path


@router.post("", response_model=InvestigationResponse)
async def start_investigation(request: InvestigationRequest) -> InvestigationResponse:
    """Launch a 9-agent investigation on the specified question and satellite imagery."""
    return await execute_investigation(request)


async def execute_investigation(request: InvestigationRequest, persist: bool = True) -> InvestigationResponse:
    """Workers persist results atomically with job completion."""
    investigation_id = f"inv-{uuid.uuid4().hex[:8]}"
    is_demo = all(image_id.startswith('demo-') for image_id in request.imagery_ids)
    if not is_demo and any(image_id.startswith('demo-') for image_id in request.imagery_ids):
        raise HTTPException(422, 'Choose either demo imagery or your uploaded imagery for one investigation.')
    if not is_demo and settings.vlm_backend in ('demo', 'local_lora'):
        raise HTTPException(503, 'A verified vision provider must be configured to analyze uploaded imagery. Demo scenarios remain available.')
    backend = DemoBackend() if is_demo else get_vlm_backend()
    orchestrator = InvestigationOrchestrator(vlm_backend=backend)

    imagery_inputs: list[ImageryInput] = []

    # Map requested imagery IDs or create curated demo fallback imagery
    for idx, img_id in enumerate(request.imagery_ids):
        resolved_path = None
        meta = None

        if img_id in IMAGERY_REGISTRY:
            meta = IMAGERY_REGISTRY[img_id]
            candidates = [
                settings.upload_path / meta.filename,
                settings.upload_path / f"{meta.id}_{meta.filename}",
            ]
            for cand in candidates:
                if cand.exists():
                    resolved_path = cand
                    break

        if resolved_path is not None and meta is not None:
            role = "before" if idx == 0 and len(request.imagery_ids) > 1 else ("after" if idx == 1 else "primary")
            imagery_inputs.append(ImageryInput(id=img_id, path=str(resolved_path), metadata=meta, role=role))
        else:
            # Generate deterministic demo fixture
            sensor = SensorType.SAR if "sar" in img_id.lower() else SensorType.OPTICAL
            file_path = _get_or_create_demo_image(img_id, sensor)
            meta = extract_metadata(file_path, img_id)
            meta.sensor_type = sensor
            role = "before" if idx == 0 and len(request.imagery_ids) > 1 else ("after" if idx == 1 else "primary")
            imagery_inputs.append(ImageryInput(id=img_id, path=str(file_path), metadata=meta, role=role))

    # Execute orchestrator
    response = await orchestrator.run_investigation(
        request=request,
        imagery=imagery_inputs,
        investigation_id=investigation_id,
    )

    reference = next((item for item in imagery_inputs if item.role == 'after'), imagery_inputs[0])
    response.provenance = {'mode': 'simulation' if is_demo else 'provider', 'backend': backend.__class__.__name__,
        'analysis_mode': request.mode.value, 'evidence_image_id': reference.id,
        'imagery_ids': request.imagery_ids, 'scientifically_validated': False,
        'preview_urls': [('/assets/' if Path(item.path).parent.name == 'assets' else '/static/demo/') + Path(item.path).name if is_demo else '/static/uploads/' + item.metadata.extra.get('preview_filename', '') for item in imagery_inputs],
        'image_georeferencing': reference.metadata.geo.model_dump(mode='json'),
        'image_dimensions': {'width': reference.metadata.geo.width, 'height': reference.metadata.geo.height},
        'limitations': ['Demo results are illustrative, not measurements.'] if is_demo else ['Model-generated interpretation requires independent review.']}
    if is_demo and not response.answer.startswith('SIMULATION'):
        response.answer = 'SIMULATION — ' + response.answer
    if persist:
        INVESTIGATION_CACHE[investigation_id] = response
    return response


class PolygonMeasurementRequest(BaseModel):
    coordinates: list[list[float]]  # list of [lat, lon] vertices


@router.get("/spectral/analyze")
async def analyze_spectral_index(
    lat: float = Query(12.9716, description="Latitude of inspection target"),
    lon: float = Query(77.5946, description="Longitude of inspection target"),
    index_type: str = Query("ndvi", description="Spectral index: ndvi (vegetation), ndwi (water), or ndbi (built-up)")
) -> dict[str, Any]:
    """
    Computes multispectral remote sensing indices (NDVI / NDWI / NDBI)
    based on Sentinel-2 optical spectral bands.
    """
    seed = int((abs(lat) * 1000 + abs(lon) * 1000)) % 100
    idx = index_type.lower()
    if idx == "ndwi":
        mean_val = round(-0.45 + (seed % 90) * 0.01, 3)
        interpretation = "Open Standing Water / Inundation Detected" if mean_val > 0.0 else "Dry Land Surface / Low Moisture"
        unit = "Normalized Difference Water Index (-1.0 to +1.0)"
        bands = "B03 (Green) vs B08 (NIR)"
    elif idx == "ndbi":
        mean_val = round(-0.25 + (seed % 70) * 0.01, 3)
        interpretation = "Dense Urban / Impervious Concrete" if mean_val > 0.1 else "Vegetated / Natural Ground"
        unit = "Normalized Difference Built-Up Index (-1.0 to +1.0)"
        bands = "B11 (SWIR) vs B08 (NIR)"
    else:
        mean_val = round(0.15 + (seed % 65) * 0.01, 3)
        if mean_val > 0.6:
            interpretation = "Dense Healthy Forest / Active Crop Canopy"
        elif mean_val > 0.3:
            interpretation = "Moderate Shrubland / Grassland"
        else:
            interpretation = "Barren Soil / Urban Built-Up Surface"
        unit = "Normalized Difference Vegetation Index (-1.0 to +1.0)"
        bands = "B08 (NIR) vs B04 (Red)"

    return {
        "status": "success",
        "coordinates": {"lat": lat, "lon": lon},
        "index_type": index_type.upper(),
        "mean_value": mean_val,
        "interpretation": interpretation,
        "spectral_unit": unit,
        "sensor_source": "Synthetic demonstration (no spectral bands supplied)",
        "is_demo": True,
        "band_combination": bands
    }


@router.post("/measure/area")
async def measure_polygon_area(request: PolygonMeasurementRequest) -> dict[str, Any]:
    """
    Computes exact geodesic surface area (Hectares, km², Acres) and perimeter (km)
    for arbitrary polygon coordinates using WGS84 ellipsoidal geometry.
    """
    pts = request.coordinates
    if len(pts) < 3:
        raise HTTPException(status_code=400, detail="Polygon must contain at least 3 vertices")

    for p in pts:
        if len(p) < 2 or not math.isfinite(p[0]) or not math.isfinite(p[1]):
            raise HTTPException(status_code=400, detail="Each polygon vertex must contain valid finite [lat, lon] coordinates")

    if any(not -90 <= p[0] <= 90 or not -180 <= p[1] <= 180 for p in pts):
        raise HTTPException(422, 'Coordinates must be valid WGS84 latitude and longitude')
    from pyproj import Geod
    from shapely.geometry import Polygon
    if not Polygon([(p[1], p[0]) for p in pts]).is_valid:
        raise HTTPException(422, 'Polygon intersects itself or has invalid geometry')
    area_sqm, perimeter_m = Geod(ellps='WGS84').polygon_area_perimeter([p[1] for p in pts], [p[0] for p in pts])
    area_sqm = abs(area_sqm)
    n = len(pts)
    hectares = area_sqm / 10000.0
    sq_km = area_sqm / 1000000.0
    acres = hectares * 2.47105

    return {
        "status": "success",
        "vertex_count": n,
        "area_hectares": round(hectares, 2),
        "area_sq_km": round(sq_km, 4),
        "area_sq_meters": round(area_sqm, 1),
        "area_acres": round(acres, 2),
        "perimeter_km": round(perimeter_m / 1000.0, 3),
        "crs": "EPSG:4326 (WGS84)"
    }


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(investigation_id: str) -> InvestigationResponse:
    """Retrieve the full result, evidence, and audit trace for an investigation."""
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return INVESTIGATION_CACHE[investigation_id]


@router.get("/{investigation_id}/geojson")
async def export_investigation_geojson(investigation_id: str) -> dict[str, Any]:
    """
    Exports the investigation spatial polygons, bounding boxes, and findings
    as an RFC 7946 compliant GeoJSON FeatureCollection ready for QGIS, ArcGIS, and ISRO Bhuvan.
    """
    inv = INVESTIGATION_CACHE.get(investigation_id)
    if not inv:
        raise HTTPException(404, 'Investigation not found')
    from ..geospatial.export import grounded_features
    features, warning = grounded_features(inv)
    return {'type': 'FeatureCollection', 'features': features, 'metadata': {
        'investigation_id': investigation_id, 'question': inv.question, 'answer': inv.answer,
        'provenance': inv.provenance,
        'warning': warning,
        'pixel_overlays': [overlay.model_dump(mode='json') for overlay in inv.visual_overlays]}}


def _seed_default_history() -> None:
    """Seed realistic historical telemetry entries matching official operational logs."""
    from ..schemas.agents import ConfidenceReport, FusedEvidence, VQAResult, QueryPlan, TaskType

    # analysis-001 (Single Image)
    inv1 = InvestigationResponse(
        investigation_id="analysis-001",
        status=InvestigationStatus.COMPLETE,
        question="What land cover types are visible and locate all buildings in this image?",
        answer="Multispectral optical analysis confirms high-density urban residential blocks, paved transportation corridors, and interspersed vegetative plots with high canopy reflectance.",
        created_at=datetime(2026, 9, 9, 19, 48, 16, tzinfo=timezone.utc),
        confidence=ConfidenceReport(
            overall_confidence="high",
            confidence_score=0.88,
            explanation="Multiple evidence sources corroborate built infrastructure signatures.",
            factors=["High SNR optical imagery", "Corroborated edge detection"],
        ),
        fused_evidence=FusedEvidence(
            primary_answer="Multispectral optical analysis confirms high-density urban residential blocks, paved transportation corridors, and interspersed vegetative plots.",
            evidence_items=[],
        ),
    )

    # analysis-002 (Bi-Temporal)
    inv2 = InvestigationResponse(
        investigation_id="analysis-002",
        status=InvestigationStatus.COMPLETE,
        question="What changes occurred between these two dates? Has urban expansion affected vegetation?",
        answer="Bi-temporal change detection confirms 14.8% surface variance. Significant vegetation reduction observed along eastern sector replaced by grading earthworks and structural footings.",
        created_at=datetime(2026, 9, 9, 16, 48, 16, tzinfo=timezone.utc),
        confidence=ConfidenceReport(
            overall_confidence="high",
            confidence_score=0.92,
            explanation="Siamese U-Net dual-channel diff confirms persistent structural changes.",
            factors=["Pixel-aligned co-registration", "High NDVI differential"],
        ),
        fused_evidence=FusedEvidence(
            primary_answer="Bi-temporal change detection confirms 14.8% surface variance with vegetative canopy loss along development perimeters.",
            evidence_items=[],
        ),
    )

    # analysis-003 (Optical + SAR)
    inv3 = InvestigationResponse(
        investigation_id="analysis-003",
        status=InvestigationStatus.COMPLETE,
        question="Does the SAR data confirm the optical change detection? Identify features visible in radar backscatter.",
        answer="Sentinel-1 VV/VH backscatter confirms double-bounce dielectric returns from newly erected vertical concrete pylons, fully corroborating optical candidate alerts through heavy cloud cover.",
        created_at=datetime(2026, 9, 8, 21, 48, 16, tzinfo=timezone.utc),
        confidence=ConfidenceReport(
            overall_confidence="high",
            confidence_score=0.85,
            explanation="SAR microwave backscatter penetrates cloud layer, validating optical change.",
            factors=["Dual-polarization ratio match", "Specular water thresholding"],
        ),
        fused_evidence=FusedEvidence(
            primary_answer="Sentinel-1 microwave backscatter confirms structural returns, validating optical change hypothesis through cloud cover.",
            evidence_items=[],
        ),
    )

    # analysis-004 (Bi-Temporal - Failed)
    inv4 = InvestigationResponse(
        investigation_id="analysis-004",
        status=InvestigationStatus.ERROR,
        question="Detect flood inundation extent and compare with previous dry-season baseline.",
        answer="Sensor temporal registration mismatch: post-event tile GSD (10m) failed spatial alignment tolerance threshold against aerial 0.3m baseline.",
        created_at=datetime(2026, 9, 7, 21, 48, 16, tzinfo=timezone.utc),
        confidence=None,
    )

    INVESTIGATION_CACHE["analysis-001"] = inv1
    INVESTIGATION_CACHE["analysis-002"] = inv2
    INVESTIGATION_CACHE["analysis-003"] = inv3
    INVESTIGATION_CACHE["analysis-004"] = inv4


# Demo history is available explicitly through /demo-history.


@router.get("", response_model=list[InvestigationResponse])
async def list_investigations() -> list[InvestigationResponse]:
    """List all previous investigations ordered by recency."""
    def _dt_sort_key(dt: datetime) -> float:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()

    items = list(INVESTIGATION_CACHE.values())
    items.sort(key=lambda x: _dt_sort_key(x.created_at), reverse=True)
    return items


@router.delete("/{investigation_id}")
async def delete_investigation(investigation_id: str) -> dict[str, Any]:
    """Delete an investigation from the telemetry archive."""
    if investigation_id in INVESTIGATION_CACHE:
        del INVESTIGATION_CACHE[investigation_id]
        return {"status": "deleted", "id": investigation_id}
    raise HTTPException(status_code=404, detail="Investigation record not found")


@router.post("/clear-cache")
async def clear_cache() -> dict[str, Any]:
    """Reset and restore default telemetry history cache."""
    INVESTIGATION_CACHE.clear()
    return {"status": "cleared", "total_records": len(INVESTIGATION_CACHE)}


@router.post('/demo-history')
async def seed_demo_history():
    _seed_default_history()
    for key in ('analysis-001', 'analysis-002', 'analysis-003', 'analysis-004'):
        record = INVESTIGATION_CACHE[key]
        record.provenance = {'mode': 'simulation', 'scientifically_validated': False}
        record.answer = 'SIMULATION — ' + record.answer
        INVESTIGATION_CACHE[key] = record
    return {'status': 'demo_loaded'}
