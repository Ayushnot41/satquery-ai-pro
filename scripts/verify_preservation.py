"""Verify source parity and byte-preserved README/media from the original snapshot."""
import ast, hashlib, json, re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'docs/preservation-manifest.json').read_text(encoding='utf-8'))
errors=[];media=0
for entry in manifest['files']:
    path=root/entry['path']
    if not path.is_file():
        errors.append('Missing original file: '+entry['path']);continue
    preserve=path.name.lower().startswith('readme') or path.suffix.lower() in {'.svg','.png','.jpg','.jpeg','.gif','.webp','.mp4','.webm','.mov','.pt','.bin','.safetensors','.pdf'}
    if preserve:
        media+=1
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            errors.append('Original asset/README changed: '+entry['path'])
original=(root/'legacy/index.html').read_text(encoding='utf-8')
enhanced=(root/'index.html').read_text(encoding='utf-8')
screens=set(re.findall(r'id="screen-([^\"]+)"',original))
functions=set(re.findall(r'(?:async\s+)?function\s+(\w+)\s*\(',original))
for screen in screens:
    if f'id="screen-{screen}"' not in enhanced:errors.append('Missing cockpit screen '+screen)
for name in functions:
    if not re.search(r'function\s+'+re.escape(name)+r'\s*\(',enhanced):errors.append('Missing cockpit function '+name)
# Compare every original route decorator, including its handler and HTTP method.
original_routes=manifest.get('api_routes',[])
if original_routes:
    for route in original_routes:
        if isinstance(route,dict) and 'handler' in route and 'file' in route:
            tree=ast.parse((root/route['file']).read_text(encoding='utf-8'))
            found=False
            for node in ast.walk(tree):
                if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name!=route['handler']:continue
                for decorator in node.decorator_list:
                    if isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Attribute) and decorator.args:
                        arg=decorator.args[0]
                        if isinstance(arg,ast.Constant) and (decorator.func.attr,arg.value)==(route['method'],route['path']):found=True
            if not found:errors.append('Missing API route '+str(route))
# A repeated top-level definition can silently shadow a function while retaining
# both FastAPI route registrations. Detect interrupted/replayed source edits.
for path in (root/'backend/app').rglob('*.py'):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'));seen=set();routes=set()
    for node in tree.body:
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
        if node.name in seen:errors.append(f'Duplicate definition: {path.relative_to(root)}:{node.name}')
        seen.add(node.name)
        for decorator in node.decorator_list:
            if isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Attribute) and decorator.func.attr in ('get','post','put','patch','delete') and decorator.args and isinstance(decorator.args[0],ast.Constant):
                key=(ast.unparse(decorator.func.value),decorator.func.attr,decorator.args[0].value)
                if key in routes:errors.append(f'Duplicate route: {path.relative_to(root)}:{key}')
                routes.add(key)
if errors:
    raise SystemExit('\n'.join(errors))
print(json.dumps({'original_files_present':len(manifest['files']),'byte_preserved_assets_and_readmes':media,'cockpit_screens':len(screens),'cockpit_functions':len(functions),'status':'passed'},indent=2))
