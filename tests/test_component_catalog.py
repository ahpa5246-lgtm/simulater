"""Distribution checks protect real assets, provenance and honest support labels."""
import hashlib
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class ComponentCatalogTests(unittest.TestCase):
    def test_distributed_catalog_has_200_distinct_credited_safe_parts(self):
        path = ROOT / 'web/vendor/components/catalog.json'
        self.assertTrue(path.is_file(), 'offline multi-source catalogue is missing')
        data = json.loads(path.read_text())
        parts = data['parts']
        self.assertGreaterEqual(len(parts), 200)
        self.assertGreaterEqual(len({p['repository'] for p in parts}), 3)
        for field in ['id', 'name', 'artworkSha256']:
            self.assertEqual(len(parts), len({p[field].casefold() for p in parts}), field)
        for p in parts:
            with self.subTest(part=p['name']):
                self.assertEqual(p['support'], 'visual-only')
                self.assertRegex(p['commit'], r'^[0-9a-f]{40}$')
                self.assertTrue(p['sourceUrl'].startswith('https://github.com/' + p['repository'] + '/blob/' + p['commit'] + '/'))
                self.assertTrue(p['license'])
                self.assertTrue(p['author'])
                self.assertIsInstance(p['connectors'], list)
                self.assertTrue(p['svgUrl'].startswith('/vendor/components/art/'))
                raw = (ROOT / 'web' / p['svgUrl'].lstrip('/')).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), p['artworkSha256'])
                svg = ET.fromstring(raw)
                self.assertTrue(len(list(svg.iter())) > 1)
                for element in svg.iter():
                    self.assertNotIn(element.tag.rsplit('}', 1)[-1], ['script', 'foreignObject', 'image', 'use'])
                    for key, val in element.attrib.items():
                        self.assertFalse(key.lower().startswith('on'))
                        self.assertNotIn('javascript:', val.lower())
        for source in data['sources']:
            self.assertTrue((ROOT/'web/vendor/components'/source['noticeFile']).is_file())
