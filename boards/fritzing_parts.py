"""Bounded Fritzing artwork import; deliberately never creates electrical models."""
import io
import os
import json
import re
import secrets
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

DEFAULT_ROOT = Path(os.environ.get('MINA_VISUAL_PARTS_DIR',Path(__file__).resolve().parents[1] / '.state' / 'visual-parts'))
SVG_NS = 'http://www.w3.org/2000/svg'
TAGS = set('svg g defs title desc path rect circle ellipse line polyline polygon text tspan linearGradient radialGradient stop clipPath'.split())
ATTRS = set('id x y x1 y1 x2 y2 dx dy cx cy r rx ry width height viewBox preserveAspectRatio d points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity font-family font-size font-weight font-style text-anchor dominant-baseline letter-spacing gradientUnits gradientTransform spreadMethod offset stop-color stop-opacity clip-path clip-rule'.split())
STYLE_ATTRS = set('fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity font-family font-size font-weight font-style text-anchor dominant-baseline letter-spacing stop-color stop-opacity clip-path clip-rule'.split())
LOCAL_URL = re.compile(r'url\(\s*[\'\"]?#[A-Za-z_][\w:.-]*[\'\"]?\s*\)', re.I)
SVG11_DOCTYPE = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'


def _xml(data, svg=False):
    # Decode before scanning so UTF-16/32 cannot hide a declaration from the check.
    try:
        if data.startswith((b'\xff\xfe\x00\x00', b'\x00\x00\xfe\xff')):
            source = data.decode('utf-32')
        elif data.startswith((b'\xff\xfe', b'\xfe\xff')):
            source = data.decode('utf-16')
        else:
            source = data.decode('utf-8-sig')
        # One exact inert declaration used by official artwork is removed before
        # parsing. No DTD is passed to ElementTree or fetched from the network.
        if svg and source.count(SVG11_DOCTYPE) == 1:
            source = source.replace(SVG11_DOCTYPE, '', 1)
        if re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b', source, re.I):
            raise ValueError('XML DTD and ENTITY declarations are forbidden.')
        return ET.fromstring(source)
    except (UnicodeError, ET.ParseError) as exc:
        raise ValueError('Invalid XML document.') from exc


def _safe_value(value):
    # No CSS escapes, at-rules, comments, external URLs, or executable expressions.
    if any(c in value for c in ('\\', '@', '<', '>', '/*', '*/')):
        return False
    remainder = LOCAL_URL.sub('', value)
    return not re.search(r'url\s*\(|expression|javascript|data:|https?:|//', remainder, re.I)


def _sanitize_svg(data):
    source = _xml(data, svg=True)
    if source.tag not in ('svg', '{%s}svg' % SVG_NS):
        raise ValueError('Breadboard image must be SVG.')
    # Rebuild using an allowlist: unknown namespaces and all active content vanish.
    clean = ET.Element('{%s}svg' % SVG_NS)
    pending = [(source, clean, 0)]
    count = 0
    while pending:
        old, new, depth = pending.pop()
        count += 1
        if count > 30000 or depth > 128:
            raise ValueError('SVG contains too many elements or nesting levels.')
        if old.text and new.tag.rsplit('}', 1)[-1] in {'text', 'tspan', 'title', 'desc'}:
            new.text = old.text
        new.tail = old.tail
        for key, value in old.attrib.items():
            if key in ATTRS and _safe_value(value):
                new.set(key, value)
            elif key in {'href', '{http://www.w3.org/1999/xlink}href'} and old.tag.rsplit('}', 1)[-1] in {'linearGradient', 'radialGradient'} and re.fullmatch(r'#[A-Za-z_][\w:.-]*', value):
                new.set('href', value)
        # Presentation attributes render under the server's strict style CSP.
        # Apply styles last, independent of XML attribute order, to retain their
        # precedence over presentation attributes in the original artwork.
        declarations = {}
        for declaration in old.get('style', '').split(';'):
            prop, sep, val = declaration.partition(':')
            prop = prop.strip().lower()
            important = bool(re.search(r'!\s*important\s*$', val, re.I))
            val = re.sub(r'!\s*important\s*$', '', val, flags=re.I).strip()
            if sep and prop in STYLE_ATTRS and val and _safe_value(val):
                if important or prop not in declarations or not declarations[prop][1]:
                    declarations[prop] = (val, important)
        for prop, (value, _) in declarations.items():
            new.set(prop, value)
        for child in old:
            tag = child.tag
            if tag.startswith('{%s}' % SVG_NS):
                tag = tag.split('}', 1)[1]
            if tag in TAGS:
                target = ET.SubElement(new, '{%s}%s' % (SVG_NS, tag))
                pending.append((child, target, depth + 1))
    ET.register_namespace('', SVG_NS)
    return ET.tostring(clean, encoding='utf-8', xml_declaration=True)


def _path(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Unsafe ZIP path.')
    return path


def import_part(data, root=None):
    """Import one .fzpz byte stream; root is the visual-parts directory itself."""
    if not isinstance(data, bytes) or not 0 < len(data) <= 1_000_000:
        raise ValueError('Part ZIP must be at most 1 MB.')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > 32 or sum(i.file_size for i in infos) > 3_000_000:
                raise ValueError('Part ZIP exceeds file or uncompressed size limits.')
            files = {}
            for info in infos:
                name = str(_path(info.filename))
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('ZIP symbolic links are forbidden.')
                if name in files:
                    raise ValueError('Duplicate ZIP path.')
                if not info.is_dir():
                    files[name] = info
            fzps = [n for n in files if n.lower().endswith('.fzp')]
            if len(fzps) != 1:
                raise ValueError('Part ZIP must contain exactly one FZP XML file.')
            part = _xml(archive.read(files[fzps[0]]))
            if part.tag != 'module':
                raise ValueError('FZP root must be module.')
            layers = part.findall('./views/breadboardView/layers')
            if len(layers) != 1 or not layers[0].get('image'):
                raise ValueError('FZP must name one breadboard SVG image.')
            image = str(_path(layers[0].get('image')))
            flattened = 'svg.' + image.replace('/', '.')
            candidates = [n for n in files if n == image or n.endswith('/' + image) or PurePosixPath(n).name == flattened]
            if len(candidates) != 1:
                raise ValueError('Breadboard SVG image must have exactly one matching ZIP file.')
            svg = _sanitize_svg(archive.read(files[candidates[0]]))
            properties = {p.get('name', ''): ''.join(p.itertext()).strip() for p in part.findall('./properties/property')}
            license_text = part.findtext('license', '').strip() or next((v for k, v in properties.items() if k.lower() == 'license'), '')
            # Attribution files are retained as inert text, never served as active markup.
            attribution = {n: archive.read(i).decode('utf-8', errors='replace') for n, i in files.items() if PurePosixPath(n).name.upper().split('.')[0] in {'LICENSE', 'COPYING', 'NOTICE', 'AUTHORS'}}
            metadata = {'id': secrets.token_hex(16), 'name': part.findtext('title', '').strip() or 'Untitled Fritzing part', 'author': part.findtext('author', '').strip(), 'license': license_text or 'Not specified; consult source attribution', 'properties': properties, 'connectors': [c.get('name', c.get('id', '')) for c in part.findall('./connectors/connector')], 'support': 'visual-only', 'attribution': attribution}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as exc:
        raise ValueError('Invalid or unsupported part ZIP.') from exc
    root = Path(root or DEFAULT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    key = metadata['id']
    metadata['svgUrl'] = '/api/visual-parts/' + key + '.svg'
    with tempfile.TemporaryDirectory(dir=root, prefix='.import-') as temporary:
        staging = Path(temporary) / key
        staging.mkdir()
        (staging / 'part.svg').write_bytes(svg)
        (staging / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
        staging.rename(root / key)
    return metadata


def svg_path(part_id, root=None):
    if not isinstance(part_id, str) or not re.fullmatch('[0-9a-f]{32}', part_id):
        raise ValueError('Invalid visual part ID.')
    root = Path(root or DEFAULT_ROOT).resolve()
    path = root / part_id / 'part.svg'
    if path.resolve() != path or not path.is_file():
        raise FileNotFoundError('Visual part not found.')
    return path


def list_parts(root=None):
    root = Path(root or DEFAULT_ROOT)
    if not root.exists():
        return []
    results = []
    for folder in sorted(root.iterdir()):
        if not re.fullmatch('[0-9a-f]{32}', folder.name) or folder.is_symlink():
            continue
        try:
            metadata = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
            if isinstance(metadata, dict) and metadata.get('id') == folder.name:
                svg_path(folder.name, root)
                results.append(metadata)
        except (OSError, ValueError, TypeError):
            continue
    return results
