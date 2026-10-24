"""Vendor uPlot 1.6.32 (MIT), with explicit lab numeric locale for portability."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];source=root/'node_modules/uplot'
p=source/'dist/uPlot.iife.min.js';s=p.read_text();old='new Intl.NumberFormat(_?k.language:"en-US")'
assert s.count(old)==1,'Review locale patch for updated upstream version'
s=s.replace(old,'new Intl.NumberFormat("en-US")')
(root/'web/vendor/uPlot.iife.min.js').write_text(s)
shutil.copyfile(source/'dist/uPlot.min.css',root/'web/vendor/uPlot.min.css')
shutil.copyfile(source/'LICENSE',root/'web/vendor/uplot-LICENSE.txt')
