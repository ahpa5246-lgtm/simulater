"""Rebuild the pinned offline Wokwi bundle/catalog from npm ci dependencies."""
from pathlib import Path
import json,re,shutil
root=Path(__file__).resolve().parents[1];out=root/'web/vendor';out.mkdir(exist_ok=True)
pkg=root/'node_modules/@wokwi/elements';version=json.loads((pkg/'package.json').read_text())['version']
if version!='1.9.2':raise SystemExit('Review upstream version before rebuilding vendor bundle')
shutil.copyfile(pkg/'dist/wokwi-elements.bundle.min.js',out/f'wokwi-elements-{version}.js')
tags=[]
for p in (pkg/'dist/esm').glob('*-element.js'):
 for tag in re.findall(r"customElement\('([^']+)'\)",p.read_text()):tags.append({'tag':tag,'name':tag.removeprefix('wokwi-').replace('-',' ').title(),'sourceFile':p.name,'status':'visual-only'})
(out/'wokwi-catalog.json').write_text(json.dumps(sorted(tags,key=lambda p:p['tag']),indent=2)+'\n')
for name in ['lit','lit-html','lit-element','@lit/reactive-element']:
 p=root/'node_modules'/name/'LICENSE'
 if p.exists():shutil.copyfile(p,out/(name.replace('/','-')+'-LICENSE.txt'))
print(f'Bundled {len(tags)} registered Wokwi elements with available dependency licenses')
