"""Fetch checksum-verified npm from its official registry to a local tool directory."""
import io, json, tarfile, urllib.request, hashlib, base64
from pathlib import Path
root = Path(__file__).resolve().parents[1] / '.tools' / 'npm'
root.mkdir(parents=True, exist_ok=True)
meta = json.load(urllib.request.urlopen('https://registry.npmjs.org/npm/11.6.2'))
with urllib.request.urlopen(meta['dist']['tarball']) as response:
    archive = response.read()
expected = meta['dist']['integrity'].split('-', 1)
assert expected[0] == 'sha512' and base64.b64encode(hashlib.sha512(archive).digest()).decode() == expected[1]
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
    tar.extractall(root, filter='data')
print('Project-local npm installed and checksum verified.')
