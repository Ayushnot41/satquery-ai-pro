"""One-time changes applied only to the enhanced clone."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
def update(name, old, new):
    p = root / name
    text = p.read_text(encoding='utf-8')
    assert old in text, name + ': source changed'
    p.write_text(text.replace(old, new), encoding='utf-8')

update('backend/app/main.py', 'from .core.config import settings', 'from .core.config import settings\nfrom .core.guard import SecurityBoundary')
p = root / 'backend/app/main.py'
s = p.read_text(encoding='utf-8')
a = s.index('    allow_origins=settings.cors_origin_list')
b = s.index('    allow_credentials=True', a)
s = s[:a] + '    allow_origins=settings.cors_origin_list,\n' + s[b:]
s = s.replace('"error": str(exc),', '"request_id": getattr(request.state, "request_id", None),')
s = s.replace('app.mount("/static/uploads", StaticFiles(directory=str(upload_path)), name="uploads")', '''@app.get('/static/uploads/{filename}')
async def private_upload(filename: str):
    from .api.imagery import IMAGERY_REGISTRY
    from .core.security import ensure_safe_path
    from fastapi import HTTPException
    if not any(filename == m.filename or filename == m.extra.get('preview_filename') for m in IMAGERY_REGISTRY.values()):
        raise HTTPException(404, 'Image not found')
    return FileResponse(ensure_safe_path(filename, str(settings.upload_path)))''')
s = s.replace('    setup_logging()', '''    if settings.environment == 'production':
        if not settings.cookie_secure or len(settings.auth_pepper) < 32 or settings.auth_pepper.startswith('development'):
            raise RuntimeError('Production requires a random AUTH_PEPPER and COOKIE_SECURE=true')
        if settings.development_verification_codes or settings.allow_demo_guest:
            raise RuntimeError('Disable guest sessions and development verification codes in production')
        if any('*' in origin or not origin.startswith('https://') for origin in settings.cors_origin_list):
            raise RuntimeError('Production CORS origins must be explicit HTTPS URLs')
    setup_logging()''')
s = s.replace('app = FastAPI(', 'app = FastAPI(').replace('# CORS middleware', 'app.add_middleware(SecurityBoundary)\n\n# CORS middleware')
s = s.replace('current.parent.parent]:', 'current.parent.parent, current.parent.parent.parent]:')
s = s.replace('    for p in [current', '    for p in [current')
s += '''\n@app.get('/console', include_in_schema=False)
async def pro_console():
    return FileResponse(PROJECT_ROOT / 'index.html')

@app.get('/legacy', include_in_schema=False)
async def legacy_console():
    return FileResponse(PROJECT_ROOT / 'legacy' / 'index.html')
'''
# Path checks for the compatibility proxy's local asset lookup.
s = s.replace('if local_asset.exists() and local_asset.is_file():', 'if local_asset.resolve().is_relative_to(next_dir.resolve()) and local_asset.exists() and local_asset.is_file():')
s = s.replace('if route_html.exists() and route_html.is_file():', 'if route_html.resolve().is_relative_to((next_dir / "server" / "app").resolve()) and route_html.exists() and route_html.is_file():')
p.write_text(s, encoding='utf-8')

update('backend/app/geospatial/raster.py', '''                if data.shape[0] in (1, 3, 4):
                    data = np.transpose(data, (1, 2, 0))
                    if data.shape[2] == 1:
                        data = data[:, :, 0]''', '''                data = np.transpose(data, (1, 2, 0))
                if data.shape[2] == 1:
                    data = data[:, :, 0]''')
update('backend/app/geospatial/raster.py', 'str(src.crs) if src.crs else "EPSG:4326"', 'str(src.crs) if src.crs else None')
update('backend/app/geospatial/raster.py', 'bounds=bounds_list,', 'bounds=bounds_list if src.crs else None,')
update('backend/app/geospatial/raster.py', 'transform=transform_list,', 'transform=transform_list if src.crs else None,')
update('backend/app/geospatial/raster.py', '''                crs="EPSG:4326",
                bounds=[77.0, 28.0, 77.1, 28.1],  # Default fallback coordinates
                transform=[0.0001, 0.0, 77.0, 0.0, -0.0001, 28.1],''', '''                crs=None,
                bounds=None,
                transform=None,''')
update('backend/app/geospatial/raster.py', 'resolution=(10.0, 10.0),', 'resolution=None,')
update('backend/app/geospatial/raster.py', '''    try:
        _, geo = load_raster_data(path)
    except Exception:
        geo = GeoMetadata(width=512, height=512, band_count=3)''', '''    _, geo = load_raster_data(path)''')
update('backend/app/geospatial/raster.py', 'satellite="Sentinel-2" if sensor == SensorType.OPTICAL else "Sentinel-1",', 'satellite=None,\n        extra={"sensor_inferred_from_filename": True, "georeferenced": bool(geo.crs)},')
update('backend/app/geospatial/raster.py', '            data = src.read()', '''            if src.width * src.height * src.count > 100_000_000:
                raise ValueError('Raster exceeds decoded size limit')
            data = src.read()''')

update('backend/app/api/imagery.py', 'IMAGERY_REGISTRY: dict[str, ImageryMetadata] = {}', 'from ..core.database import DurableStore\nIMAGERY_REGISTRY = DurableStore("imagery", ImageryMetadata)')
update('backend/app/api/imagery.py', 'uuid.uuid4().hex[:8]', 'uuid.uuid4().hex')
update('backend/app/api/imagery.py', 'async def upload_image(', 'def upload_image(')
update('backend/app/api/imagery.py', 'if file_size > settings.max_upload_bytes:', 'if file_size <= 0 or file_size > settings.max_upload_bytes:')
update('backend/app/api/imagery.py', '''        IMAGERY_REGISTRY[image_id] = metadata''', '''        from ..geospatial.raster import load_raster_data
        from PIL import Image
        import numpy as np
        pixels, _ = load_raster_data(target_path)
        if pixels.ndim == 3:
            pixels = pixels[:, :, :3] if pixels.shape[2] >= 3 else pixels[:, :, 0]
        if pixels.dtype != np.uint8:
            finite = np.nan_to_num(pixels.astype(float))
            lo, hi = np.percentile(finite, [2, 98])
            pixels = (np.clip((finite - lo) / max(hi - lo, 1e-9), 0, 1) * 255).astype(np.uint8)
        preview_name = f'{image_id}_preview.png'
        preview = Image.fromarray(pixels)
        preview.thumbnail((1600, 1600))
        preview.save(upload_dir / preview_name)
        metadata.extra['preview_filename'] = preview_name
        IMAGERY_REGISTRY[image_id] = metadata''')
update('backend/app/api/imagery.py', 'preview_url=f"/static/uploads/{target_path.name}",', 'preview_url=f"/static/uploads/{preview_name}",\n            warnings=[] if metadata.geo.crs else ["No georeferencing: geographic measurements and exports are unavailable."],')
update('backend/app/api/imagery.py', '''        raise HTTPException(status_code=500, detail=f"Failed to process imagery metadata: {e}")''', '''        target_path.unlink(missing_ok=True)
        (upload_dir / f'{image_id}_preview.png').unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail='Image could not be decoded. Upload a valid supported raster.')''')

update('backend/app/api/investigation.py', 'INVESTIGATION_CACHE: dict[str, InvestigationResponse] = {}', 'from ..core.database import DurableStore\nINVESTIGATION_CACHE = DurableStore("investigations", InvestigationResponse)')
update('backend/app/api/investigation.py', '    file_path = demo_dir / f"{name}.png"', '''    import re
    if not re.fullmatch(r'demo-[a-zA-Z0-9_-]{1,100}', name):
        raise HTTPException(404, 'Image not found in this workspace')
    file_path = demo_dir / f"{name}.png"''')
p = root / 'backend/app/api/investigation.py'
s = p.read_text(encoding='utf-8')
a = s.index('        if resolved_path is None:\n            # Look on disk')
b = s.index('        if resolved_path is not None and meta is not None:', a)
s = s[:a] + s[b:]
s = s.replace('    backend = get_vlm_backend()', '''    is_demo = all(image_id.startswith('demo-') for image_id in request.imagery_ids)
    if not is_demo and any(image_id.startswith('demo-') for image_id in request.imagery_ids):
        raise HTTPException(422, 'Choose either demo imagery or your uploaded imagery for one investigation.')
    if not is_demo and settings.vlm_backend in ('demo', 'local_lora'):
        raise HTTPException(503, 'A verified vision provider must be configured to analyze uploaded imagery. Demo scenarios remain available.')
    backend = DemoBackend() if is_demo else get_vlm_backend()''')
s = s.replace('    INVESTIGATION_CACHE[investigation_id] = response', '''    response.provenance = {'mode': 'simulation' if is_demo else 'provider', 'backend': backend.__class__.__name__,
        'imagery_ids': request.imagery_ids, 'scientifically_validated': False,
        'limitations': ['Demo results are illustrative, not measurements.'] if is_demo else ['Model-generated interpretation requires independent review.']}
    if is_demo and not response.answer.startswith('SIMULATION'):
        response.answer = 'SIMULATION — ' + response.answer
    INVESTIGATION_CACHE[investigation_id] = response''')
s = s.replace('"sensor_source": "Sentinel-2 MSI (10m Resolution)",', '"sensor_source": "Synthetic demonstration (no spectral bands supplied)",\n        "is_demo": True,')
s = s.replace('# Initialize demo telemetry cache\n_seed_default_history()', '# Demo history is available explicitly through /demo-history.')
s = s.replace('    _seed_default_history()\n    return {"status": "cleared"', '    return {"status": "cleared"')
s += '''\n@router.post('/demo-history')
async def seed_demo_history():
    _seed_default_history()
    for key in ('analysis-001', 'analysis-002', 'analysis-003', 'analysis-004'):
        record = INVESTIGATION_CACHE[key]
        record.provenance = {'mode': 'simulation', 'scientifically_validated': False}
        record.answer = 'SIMULATION — ' + record.answer
        INVESTIGATION_CACHE[key] = record
    return {'status': 'demo_loaded'}
'''
a = s.index('    # Geodesic Shoelace Formula')
b = s.index('    hectares = area_sqm / 10000.0', a)
s = s[:a] + '''    if any(not -90 <= p[0] <= 90 or not -180 <= p[1] <= 180 for p in pts):
        raise HTTPException(422, 'Coordinates must be valid WGS84 latitude and longitude')
    from pyproj import Geod
    from shapely.geometry import Polygon
    if not Polygon([(p[1], p[0]) for p in pts]).is_valid:
        raise HTTPException(422, 'Polygon intersects itself or has invalid geometry')
    area_sqm, perimeter_m = Geod(ellps='WGS84').polygon_area_perimeter([p[1] for p in pts], [p[0] for p in pts])
    area_sqm = abs(area_sqm)
    n = len(pts)
''' + s[b:]
a = s.index('    inv = INVESTIGATION_CACHE.get(investigation_id)', s.index('async def export_investigation_geojson'))
b = s.index('\n\ndef _seed_default_history()', a)
s = s[:a] + '''    inv = INVESTIGATION_CACHE.get(investigation_id)
    if not inv:
        raise HTTPException(404, 'Investigation not found')
    # Pixel overlays cannot be emitted as geographic coordinates without a verified transform.
    # Preserve export functionality and return evidence explicitly as non-geographic properties.
    return {'type': 'FeatureCollection', 'features': [], 'metadata': {
        'investigation_id': investigation_id, 'question': inv.question, 'answer': inv.answer,
        'provenance': inv.provenance,
        'warning': 'No verified geospatial grounding. Pixel overlays are retained in the JSON report.',
        'pixel_overlays': [overlay.model_dump(mode='json') for overlay in inv.visual_overlays]}}
''' + s[b:]
p.write_text(s, encoding='utf-8')
update('backend/app/schemas/investigation.py', '    answer: str = ""', '    answer: str = ""\n    provenance: dict = Field(default_factory=dict)')
print('Foundation upgraded.')
