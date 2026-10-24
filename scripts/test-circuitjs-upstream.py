"""Verify every vendored asset and run the pinned upstream solver test suite."""
import hashlib,json,subprocess,tarfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];meta=json.loads((root/'third_party/circuitjs/manifest.json').read_text());source=root/'third_party/circuitjs/source.tar.gz'
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['sourceSha256']
for name,digest in meta['files'].items():assert hashlib.sha256((root/'web/circuitjs'/name).read_bytes()).hexdigest()==digest,name
work=root/'.tools/circuitjs-test'
if work.exists():shutil.rmtree(work)
work.mkdir(parents=True)
with tarfile.open(source) as archive:archive.extractall(work,filter='data')
subprocess.run(['node',str(root/'node_modules/vitest/vitest.mjs'),'run','--root',str(work/'ts'),'--config',str(root/'circuitjs-vitest.config.mjs')],cwd=root,check=True)
print(f'Verified {len(meta["files"])} pinned offline assets and source archive')
