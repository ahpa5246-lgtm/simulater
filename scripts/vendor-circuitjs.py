"""Rebuild pinned GPL CircuitJS. Requires npm and git; generated assets work offline."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'third_party/circuitjs/source.tar.gz'
work=root/'.tools/circuitjs-build'
if work.exists():shutil.rmtree(work)
work.mkdir(parents=True)
with tarfile.open(source) as archive:archive.extractall(work,filter='data')
ts=work/'ts'
p=ts/'circuitjs.html'
lines=p.read_text().splitlines()
p.write_text('\n'.join(x for x in lines if 'manifest' not in x and 'dropbox.com/static' not in x)+'\n')
p=ts/'main.ts';s=p.read_text();a=s.index('// Registered only');b=s.index('const app = new CirSim();',a);p.write_text(s[:a]+s[b:])
# This local server has neither Dropbox credentials nor a PHP URL-shortening service.
p=ts/'Menus.ts';s=p.read_text();s=s.replace('        fileMenu.addMenuItem(this.importFromDropboxItem,\n            iconHtml("dropbox", "Import From Dropbox..."), "file", "importfromdropbox");','');p.write_text(s)
p=ts/'CommandPaletteRegistry.ts';p.write_text('\n'.join(x for x in p.read_text().splitlines() if 'file:importfromdropbox' not in x)+'\n')
p=ts/'ExportAsUrlDialog.ts';p.write_text(p.read_text().replace('shortRelaySupported = true','shortRelaySupported = false'))
p=ts/'circuitjs.html';p.write_text(p.read_text().replace('<title>CircuitJS</title>','<title>Mina · CircuitJS</title>').replace('</body>','<a class="mina-home" href="/university.html">← Mina laboratory</a></body>'))
p=ts/'style.css';p.write_text(p.read_text()+'\n.mina-home{position:fixed;right:12px;bottom:12px;z-index:10000;padding:8px 14px;background:#17382b;color:#bbf3ca;border:1px solid #508267;border-radius:6px;font:12px system-ui;text-decoration:none}\n')
subprocess.run(['npm','ci','--no-audit','--no-fund'],cwd=ts,check=True)
subprocess.run(['npm','run','build'],cwd=ts,check=True)
out=root/'web/circuitjs'
if out.exists():shutil.rmtree(out)
shutil.copytree(ts/'dist',out)
shutil.copyfile(work/'COPYING.txt',root/'third_party/circuitjs/COPYING.txt')
files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(root/'third_party/circuitjs/manifest.json').write_text(json.dumps({'upstream':'https://github.com/pfalstad/circuitjs1','commit':'778723096a46f3c5ce4e11bd9edc24324754f02c','license':'GPL-2.0-or-later','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'integration':'Remove external Dropbox loader/menu, unsupported short-URL service, site-specific manifest and service-worker registration; add return link. Solver unchanged. See scripts/vendor-circuitjs.py.','files':files},indent=2)+'\n')
print(f'Vendored {len(files)} files')
