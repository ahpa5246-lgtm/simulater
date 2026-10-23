"""Build a credited, deterministic, visual-only library from local git checkouts.
Usage: python scripts/vendor-components.py /tmp/mina-component-sources
No network access is performed. See generated provenance and rejection report.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from urllib.parse import quote
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from boards.fritzing_parts import _xml, _sanitize_svg

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ('adafruit', 'adafruit/Fritzing-Library', 'CC-BY-SA-3.0', 'LICENSE'),
    ('sparkfun', 'sparkfun/Fritzing_Parts', 'CC-BY-SA-4.0', 'License.md'),
    ('seeed', 'Seeed-Studio/fritzing_parts', 'CC-BY-SA-4.0', 'README.md'),
]

def category(name):
    name = name.lower()
    for group, words in [
        ('Sensors', 'sensor accelerometer gyroscope magnetometer barometer thermometer temperature humidity pressure proximity ultrasonic gas imu loadcell'.split()),
        ('Displays & LEDs', 'display oled lcd led neopixel matrix screen'.split()),
        ('Motors & drivers', 'motor servo stepper driver actuator'.split()),
        ('Communication', 'wifi bluetooth radio lora rfid nfc gps ethernet transceiver'.split()),
        ('Power', 'battery power charger regulator solar lipo'.split()),
        ('Boards & controllers', 'arduino feather xiao controller microcontroller raspberry esp32 trinket metro board micro:bit seeeduino'.split()),
        ('Inputs & controls', 'button switch joystick potentiometer encoder keypad touch'.split()),
    ]:
        if any(re.search(r'(?<![a-z0-9])'+re.escape(word)+r'(?:s)?(?![a-z0-9])', name) for word in words):
            return group
    return 'Modules & components'

def documents(path, root):
    if path.suffix.lower() == '.fzpz':
        if path.stat().st_size > 3_000_000:
            raise ValueError('archive exceeds build limit')
        with zipfile.ZipFile(path) as z:
            if len(z.infolist()) > 64 or sum(i.file_size for i in z.infolist()) > 8_000_000:
                raise ValueError('archive expansion exceeds build limit')
            files = z.namelist()
            fzps = [n for n in files if n.lower().endswith('.fzp')]
            if len(fzps) != 1:
                raise ValueError('requires one part definition')
            part = _xml(z.read(fzps[0]))
            image = part.find('./views/breadboardView/layers').get('image')
            candidates = [n for n in files if n == image or n.endswith('/'+image) or Path(n).name == 'svg.'+image.replace('/', '.')]
            if len(candidates) != 1:
                raise ValueError('missing or ambiguous breadboard SVG')
            return part, z.read(candidates[0])
    part = _xml(path.read_bytes())
    image = part.find('./views/breadboardView/layers').get('image')
    candidates = [path.parent/image, path.parent/('svg.'+image.replace('/', '.')), root/'svg'/image]
    found = list(dict.fromkeys(p for p in candidates if p.is_file()))
    if len(found) != 1:
        raise ValueError('missing or ambiguous standalone SVG')
    return part, found[0].read_bytes()

def main(source_root):
    dest = ROOT/'web/vendor/components'
    (dest/'art').mkdir(parents=True, exist_ok=True)
    (dest/'notices').mkdir(exist_ok=True)
    parts, sources, skipped = [], [], []
    names, artwork = set(), set()
    for key, repo, license_id, notice in SOURCES:
        checkout = source_root/key
        commit = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
        notice_file = 'notices/'+key+'.txt'
        credits = (checkout/notice).read_text(errors='replace')
        if notice != 'README.md':
            credits += '\n\n--- Upstream README / additional art credits ---\n'+(checkout/'README.md').read_text(errors='replace')
        (dest/notice_file).write_text(credits)
        count = 0
        files = sorted(p for p in checkout.rglob('*') if p.suffix.lower() in {'.fzp', '.fzpz'} and '.git' not in p.parts)
        for path in files:
            if count >= 110:
                break
            relative = path.relative_to(checkout).as_posix()
            try:
                part, raw = documents(path, checkout)
                name = ' '.join(part.findtext('title', '').split())
                if not name:
                    raise ValueError('missing title')
                normalized = re.sub(r'\W+', '', name.casefold())
                if normalized in names:
                    raise ValueError('duplicate product title')
                svg = _sanitize_svg(raw)
                digest = hashlib.sha256(svg).hexdigest()
                if digest in artwork:
                    raise ValueError('duplicate artwork')
                node = _xml(svg, svg=True)
                if len(list(node.iter())) < 3:
                    raise ValueError('empty sanitized artwork')
                ident = key+'-'+hashlib.sha256(relative.encode()).hexdigest()[:16]
                (dest/'art'/(ident+'.svg')).write_bytes(svg)
                props = {p.get('name',''): ''.join(p.itertext()).strip() for p in part.findall('./properties/property')}
                parts.append({'id': ident, 'name': name, 'category': category(name), 'repository': repo, 'commit': commit, 'sourcePath': relative, 'sourceUrl': 'https://github.com/'+repo+'/blob/'+commit+'/'+quote(relative, safe='/'), 'author': part.findtext('author','').strip() or repo.split('/')[0], 'license': license_id, 'licenseUrl': 'https://creativecommons.org/licenses/by-sa/'+('3.0' if license_id.endswith('3.0') else '4.0')+'/', 'originalLicense': part.findtext('license','').strip(), 'noticeUrl': '/vendor/components/'+notice_file, 'connectors': [{'id': c.get('id',''), 'name': c.get('name',''), 'type': c.get('type','')} for c in part.findall('./connectors/connector')], 'properties': props, 'support': 'visual-only', 'svgUrl': '/vendor/components/art/'+ident+'.svg', 'artworkSha256': digest, 'changes': 'Static SVG allowlist sanitization; active content and unsupported SVG features removed. Metadata extracted; no electrical simulation model added.'})
                names.add(normalized)
                artwork.add(digest)
                count += 1
            except (ValueError, AttributeError, KeyError, zipfile.BadZipFile) as e:
                skipped.append({'repository': repo, 'path': relative, 'reason': str(e)})
        sources.append({'repository': repo, 'commit': commit, 'license': license_id, 'noticeFile': notice_file, 'count': count})
    parts.sort(key=lambda p: p['name'].casefold())
    (dest/'catalog.json').write_text(json.dumps({'schemaVersion': 1, 'parts': parts, 'sources': sources}, ensure_ascii=False, indent=2)+'\n')
    (dest/'build-report.json').write_text(json.dumps({'accepted': len(parts), 'sources': sources, 'skipped': skipped}, indent=2)+'\n')
    print(json.dumps({'accepted': len(parts), 'sources': sources, 'skipped': len(skipped)}, indent=2))
    if len(parts) < 200 or any(s['count'] == 0 for s in sources):
        raise SystemExit('Insufficient distinct parts or source diversity')

if __name__ == '__main__':
    main(Path(sys.argv[1]))
