from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Existing integration tests now explicitly establish an isolated demo session.
for p in (root/'backend/tests').glob('test_*.py'):
 s=p.read_text(encoding='utf-8');lines=[]
 for line in s.splitlines():
  lines.append(line)
  if 'async with ' in line and 'AsyncClient(' in line and ' as client:' in line:
   lines.append(' '*(len(line)-len(line.lstrip())+4)+"await client.post('/api/auth/guest-token', json={})")
 p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=root/'backend/tests/test_agents.py';s=p.read_text(encoding='utf-8').replace('async def test_input_validation():','async def test_input_validation(tmp_path):').replace('    # Using existing test file','    from PIL import Image\n    path = tmp_path / "input.png"\n    Image.new("RGB", (256, 256)).save(path)').replace('path="g:/Satquery Ai/.gitignore"','path=str(path)');p.write_text(s,encoding='utf-8')
p=root/'backend/tests/test_api.py';s=p.read_text(encoding='utf-8')
s=s.replace('from app.api.auth import DEMO_USERS_DB','from app.api.auth import USERS as DEMO_USERS_DB').replace('== "LEVEL_4_TOP_SECRET"','== "PUBLIC"').replace('assert r_goog.status_code == 200','assert r_goog.status_code == 503').replace('        assert r_goog.json()["user"]["google_verified"] is True','        assert "access_token" not in r_goog.json()').replace('get("demo_otp_hint")','get("development_code")').replace('assert r_master.status_code == 200','assert r_master.status_code == 400').replace('        assert r_master.json()["verified"] is True','        assert "access_token" not in r_master.json()')
a=s.index('        response = await client.get("/api/investigate/inv-test/geojson")');b=s.index('\n\n@pytest',a)
s=s[:a]+'''        response = await client.get('/api/investigate/inv-test/geojson')
        assert response.status_code == 404
        result = await client.post('/api/investigate', json={'question':'Describe construction', 'imagery_ids':['demo-construction-before']})
        response = await client.get('/api/investigate/' + result.json()['investigation_id'] + '/geojson')
        assert response.status_code == 200
        assert response.json()['type'] == 'FeatureCollection'
        assert response.json()['features'] == []
        assert response.json()['metadata']['provenance']['mode'] == 'simulation'
''' + s[b:];p.write_text(s,encoding='utf-8')
p=root/'backend/tests/test_benchmark_history.py';s=p.read_text(encoding='utf-8').replace('        # 1. Get history list', "        await client.post('/api/investigate/demo-history')\n        # 1. Get history list").replace('        # 3. Delete an item',"        assert (await client.get('/api/investigate')).json() == []\n        await client.post('/api/investigate/demo-history')\n        # 3. Delete an item");p.write_text(s,encoding='utf-8')
# Make the NASA contract test deterministic while validating the exact upstream request.
p=root/'backend/tests/test_nasa_tile.py';s=p.read_text(encoding='utf-8').replace('async def test_nasa_tile_proxy_valid_layer():','async def test_nasa_tile_proxy_valid_layer(monkeypatch):')
needle='async def test_nasa_tile_proxy_valid_layer(monkeypatch):'
s=s.replace(needle,needle+'''
    import httpx
    original_get=httpx.AsyncClient.get
    async def upstream(self,url,**kwargs):
        if str(url).startswith('https://gibs.earthdata.nasa.gov/'):
            assert '/2024-01-15/' in str(url)
            assert '/4/6/11.jpg' in str(url)
            return httpx.Response(200, content=b'\\xff\\xd8'+b'x'*2048,headers={'content-type':'image/jpeg'})
        return await original_get(self,url,**kwargs)
    monkeypatch.setattr(httpx.AsyncClient,'get',upstream)
''');p.write_text(s,encoding='utf-8')
print('Existing integration coverage migrated to real sessions and honest contracts.')
