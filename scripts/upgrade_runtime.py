from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'backend/app/models/gateway_backend.py';s=p.read_text(encoding='utf-8')
a=s.index('            logger.warning("all_gateways_failed_using_synthesis"');b=s.index('\n    async def generate_caption',a)
s=s[:a]+'''            logger.warning('vision_providers_unavailable', model=self._model)
            raise RuntimeError('Vision providers unavailable; no inference was completed') from exc
''' + s[b:]
a=s.index('            logger.warning("text_inference_fallback"');b=s.index('\n    async def health_check',a)
s=s[:a]+'''            logger.warning('text_providers_unavailable', model=model)
            raise RuntimeError('Text providers unavailable; no inference was completed') from exc
''' + s[b:];p.write_text(s,encoding='utf-8')
p=root/'backend/app/api/nasa_tile.py';s=p.read_text(encoding='utf-8')
a=s.index('    # Clamp zoom');b=s.index('\n\n@router.get("/layers")',a)
s=s[:a]+'''    from datetime import date as CalendarDate
    try:
        CalendarDate.fromisoformat(date)
    except ValueError:
        raise HTTPException(422, 'Invalid date; use YYYY-MM-DD')
    max_z = LAYER_MAX_ZOOM[layer]
    if z > max_z or x >= 2**z or y >= 2**z:
        raise HTTPException(422, f'Tile coordinates exceed this layer grid (maximum zoom {max_z})')
    tile_url = f'{GIBS_BASE}/{layer}/default/{date}/GoogleMapsCompatible_Level{max_z}/{z}/{y}/{x}.jpg'
    headers = {'User-Agent': 'Satquery-AI-Pro/1.0'}
    if settings.nasa_earthdata_token:
        headers['Authorization'] = f'Bearer {settings.nasa_earthdata_token}'
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            response = await client.get(tile_url, headers=headers)
        if response.status_code != 200 or not response.headers.get('content-type', '').startswith('image/'):
            raise HTTPException(404 if response.status_code == 404 else 502, 'Requested NASA layer/date is unavailable. No substitute imagery was returned.')
        return Response(response.content, media_type=response.headers['content-type'], headers={
            'X-NASA-Layer': layer, 'X-Tile-Date': date, 'X-Data-Source': 'NASA GIBS', 'Cache-Control': 'public, max-age=3600'})
    except httpx.TimeoutException:
        raise HTTPException(504, 'NASA imagery request timed out')
    except httpx.RequestError:
        raise HTTPException(502, 'NASA imagery service unavailable')
''' + s[b:];p.write_text(s,encoding='utf-8')
# Preserve the architecture and artifact; never treat random initialization as trained inference.
p=root/'backend/app/models/siamese_unet.py';s=p.read_text(encoding='utf-8')
s=s.replace('    if TORCH_AVAILABLE and torch is not None:', "    if TORCH_AVAILABLE and torch is not None and __import__('os').environ.get('VERIFIED_SIAMESE_CHECKPOINT'):")
s=s.replace('            model.eval()', '''            checkpoint = torch.load(__import__('os').environ['VERIFIED_SIAMESE_CHECKPOINT'], map_location=dev, weights_only=True)
            state = checkpoint.get('state_dict', checkpoint)
            model.load_state_dict(state, strict=True)
            model.eval()''')
s=s.replace('"model_name": "Siamese-UNet-ResNet18-DeepChange",', '''"model_name": "Siamese-UNet" if mode_used.startswith('torch') else "Classical spectral-gradient difference",
        "trained_model_used": mode_used.startswith('torch'),''')
p.write_text(s,encoding='utf-8')
# Never expose arbitrary source files through either compatibility development server.
for name in ['server.js','frontend/server.js']:
 p=root/name;s=p.read_text(encoding='utf-8')
 marker="  const pathname = parsedUrl.pathname || '/';"
 if marker in s:
  s=s.replace(marker,marker+'''
  const allowed = pathname === '/' || pathname === '/app' || pathname === '/index.html' || pathname === '/bhuvision_preview.html' || pathname === '/manifest.json' || pathname === '/console' || pathname === '/legacy' || pathname.startsWith('/assets/') || pathname.startsWith('/api/') || pathname.startsWith('/static/') || pathname.startsWith('/docs/') || pathname.startsWith('/_next/');
  if (!allowed || decodeURIComponent(pathname).split('/').some(part => part === '..' || part.startsWith('.'))) {
    res.writeHead(404, {'Content-Type':'text/plain'});res.end('Not found');return;
  }
''')
  s=s.replace("process.env.PORT || '3000'","process.env.PORT || '3010'").replace("process.env.BACKEND_PORT || '8000'","process.env.BACKEND_PORT || '8010'")
  p.write_text(s,encoding='utf-8')
print('Provider failures, scientific provenance and compatibility-server boundaries updated.')
