"""Record the original project contract before enhancements; never run against the source."""
from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '8d26496c130127dba93dad55fb7a88f418fe3d84'
manifest_path = ROOT / 'docs' / 'preservation-manifest.json'
if manifest_path.exists():
    raise SystemExit('Preservation manifest already exists; baseline is immutable.')
files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
records = []
for name in filter(None, files):
    data = (ROOT / name).read_bytes()
    records.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
screens = sorted(set(re.findall(r'id="screen-([\w-]+)"', (ROOT/'index.html').read_text(encoding='utf-8'))))
functions = sorted(set(re.findall(r'(?:async\s+)?function\s+(\w+)\s*\(', (ROOT/'index.html').read_text(encoding='utf-8'))))
routes = []
for file in (ROOT/'backend/app/api').glob('*.py'):
    tree = ast.parse(file.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in {'get','post','put','patch','delete'}:
                    routes.append({'file': file.relative_to(ROOT).as_posix(), 'handler': node.name, 'method': dec.func.attr, 'path': ast.literal_eval(dec.args[0]) if dec.args else ''})
manifest_path.write_text(json.dumps({'baseline_commit':BASE,'files':records,'screens':screens,'javascript_functions':functions,'api_routes':routes},indent=2),encoding='utf-8')
(ROOT/'legacy').mkdir(exist_ok=True)
for name in ['index.html','bhuvision_preview.html','README.md']:
    shutil.copy2(ROOT/name, ROOT/'legacy'/name)
source_vendor = ROOT.parent/'assets/vendor'
if source_vendor.exists():
    shutil.copytree(source_vendor, ROOT/'assets/vendor', dirs_exist_ok=True)
print(json.dumps({'files_preserved':len(records),'screens':screens,'javascript_functions':len(functions),'api_routes':len(routes)}))
