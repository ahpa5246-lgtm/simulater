"""Visual-only Fritzing ZIP security and persistence tests."""
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from boards.fritzing_parts import import_part, list_parts, svg_path

# Official fritzing/fritzing-parts at 27535f2fd02097be9bed229b75aa8e9be282a4a0.
# core/LED-generic-3mm.fzp: Stefan Hermann. Graphics: Fritzing, CC BY-SA 3.0.
# Source and attribution links are documented in docs/fritzing-import.md.
OFFICIAL_FZP = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><module fritzingVersion=\"0.1.beta.1396\" moduleId=\"3mmColorLEDModuleID\">\n <version>4</version>\n <author>Stefan Hermann</author>\n <title>Red LED - 3mm</title>\n <label>LED</label>\n <date>2008-10-10</date>\n <tags>\n  <tag>LED</tag>\n  <tag>Red LED</tag>\n  <tag>indicator</tag>\n  <tag>fritzing core</tag>\n </tags>\n <properties>\n  <property name=\"package\">3 mm [THT]</property>\n  <property name=\"family\">LED</property>\n  <property name=\"color\" showInLabel=\"yes\">Red (633nm)</property>\n  <property name=\"current\">0.030A</property>\n  <property name=\"leg\" >yes</property>\n </properties>\n <description>A generic red LED (~1.8V)</description>\n <spice>\n  <model>*Typ RED,GREEN,YELLOW,AMBER GaAs LED: Vf=2.1V Vr=4V If=40mA trr=3uS</model>\n  <model>.MODEL LED_GENERIC D (IS=93.1P RS=42M N=4.61 BV=9 IBV=10U CJO=2.97P VJ=.75 M=.333 TT=4.32U)</model>\n  <line>D{instanceTitle} {net connector1} {net connector0} LED_GENERIC</line>\n </spice>\n <views>\n  <iconView>\n   <layers image=\"icon/LED-red-5mmicon.svg\">\n    <layer layerId=\"icon\"/>\n   </layers>\n  </iconView>\n  <breadboardView fliphorizontal=\"true\" flipvertical=\"true\">\n   <layers image=\"breadboard/LED-3mm-red-leg.svg\">\n    <layer layerId=\"breadboard\"/>\n   </layers>\n  </breadboardView>\n  <schematicView>\n   <layers image=\"schematic/led.svg\">\n    <layer layerId=\"schematic\"/>\n   </layers>\n  </schematicView>\n  <pcbView>\n   <layers image=\"pcb/3mm_LED.svg\">\n    <layer layerId=\"copper0\"/>\n    <layer layerId=\"keepout\"/>\n    <layer layerId=\"soldermask\"/>\n    <layer layerId=\"silkscreen\"/>\n    <layer layerId=\"outline\"/>\n   <layer layerId=\"copper1\"/></layers>\n  </pcbView>\n </views>\n <connectors>\n  <connector id=\"connector0\" name=\"cathode\" type=\"male\">\n   <description>cathode pin</description>\n   <views>\n    <breadboardView>\n     <p layer=\"breadboard\" svgId=\"connector0pin\"  legId=\"connector0leg\"/>\n    </breadboardView>\n    <schematicView>\n     <p layer=\"schematic\" svgId=\"connector0pin\" terminalId=\"connector0terminal\"/>\n    </schematicView>\n    <pcbView>\n     <p layer=\"copper0\" svgId=\"connector0pad\"/>\n    <p layer=\"copper1\" svgId=\"connector0pad\"/></pcbView>\n   </views>\n  </connector>\n  <connector id=\"connector1\" name=\"anode\" type=\"male\">\n   <description>anode pin</description>\n   <views>\n    <breadboardView>\n     <p layer=\"breadboard\" svgId=\"connector1pin\"  legId=\"connector1leg\"/>\n    </breadboardView>\n    <schematicView>\n     <p layer=\"schematic\" svgId=\"connector1pin\" terminalId=\"connector1terminal\"/>\n    </schematicView>\n    <pcbView>\n     <p layer=\"copper0\" svgId=\"connector1pad\"/>\n    <p layer=\"copper1\" svgId=\"connector1pad\"/></pcbView>\n   </views>\n  </connector>\n </connectors>\n</module>\n"
OFFICIAL_SVG = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<!-- Generator: Adobe Illustrator 14.0.0, SVG Export Plug-In . SVG Version: 6.00 Build 43363)  -->\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n<svg version=\"1.1\" id=\"Layer_1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" x=\"0px\" y=\"0px\"\n\t width=\"15.456px\" height=\"29.207px\" viewBox=\"0 0 15.456 29.207\" enable-background=\"new 0 0 15.456 29.207\" xml:space=\"preserve\">\n<g id=\"breadboard\">\n\t<rect id=\"connector0pin\" x=\"3.451\" y=\"25.421\" fill=\"none\" width=\"2.151\" height=\"0.72\"/>\n\t<rect id=\"connector1pin\" x=\"10.651\" y=\"25.421\" fill=\"none\" width=\"2.154\" height=\"0.72\"/>\n\t\n\t\t<line id=\"connector0leg\" fill=\"none\" stroke=\"#8C8C8C\" stroke-width=\"1.988\" stroke-linecap=\"round\" x1=\"4.527\" y1=\"29.207\" x2=\"4.527\" y2=\"53.822\"/>\n\t\n\t\t<line id=\"connector1leg\" fill=\"none\" stroke=\"#8C8C8C\" stroke-width=\"1.988\" stroke-linecap=\"round\" x1=\"11.729\" y1=\"29.207\" x2=\"11.729\" y2=\"53.822\"/>\n\t<rect x=\"3.451\" y=\"19.379\" fill=\"#8C8C8C\" width=\"2.151\" height=\"9.828\"/>\n\t<path fill=\"#8C8C8C\" d=\"M12.805,29.207c0-1.174-1.065-2.103-2.089-2.992c-0.416-0.367-1.199-1.001-1.199-1.424V19.32H7.356V25.1\n\t\tc0,1.059,0.947,1.879,1.946,2.748c0.444,0.377,1.349,1.25,1.349,1.771\"/>\n\t<g id=\"g12\">\n\t\t<path id=\"color_path14\" opacity=\"0.3\" fill=\"#E60000\" enable-background=\"new    \" d=\"M11.694,14.099V9.8\n\t\t\tc0-2.845-2.303-5.153-5.151-5.153C3.698,4.647,1.39,6.951,1.39,9.8v9.921c1.071,1.201,2.979,2.001,5.153,2.001\n\t\t\tc3.359,0,6.083-1.902,6.083-4.26v-1.107C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t<path id=\"path16\" opacity=\"0.5\" fill=\"#E6E6E6\" enable-background=\"new    \" d=\"M11.694,14.099V9.8\n\t\t\tc0-2.845-2.303-5.153-5.151-5.153C3.698,4.647,1.39,6.951,1.39,9.8v9.921c1.071,1.201,2.979,2.001,5.153,2.001\n\t\t\tc3.359,0,6.083-1.902,6.083-4.26v-1.107C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t<path id=\"path18\" opacity=\"0.9\" fill=\"#D1D1D1\" enable-background=\"new    \" d=\"M11.694,14.099v2.257\n\t\t\tc0,1.991-2.301,3.608-5.151,3.608c-2.845,0-5.153-1.612-5.153-3.608v2.257v1.109c1.071,1.2,2.979,2,5.153,2\n\t\t\tc3.359,0,6.083-1.902,6.083-4.26v-1.106C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t<path id=\"color_path20\" opacity=\"0.7\" fill=\"#E60000\" enable-background=\"new    \" d=\"M11.694,14.099v2.257\n\t\t\tc0,1.991-2.301,3.608-5.151,3.608c-2.845,0-5.153-1.612-5.153-3.608v2.257v1.109c1.071,1.2,2.979,2,5.153,2\n\t\t\tc3.359,0,6.083-1.902,6.083-4.26v-1.106C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t<path id=\"color_path22\" opacity=\"0.25\" fill=\"#E60000\" enable-background=\"new    \" d=\"M11.694,14.099v2.257\n\t\t\tc0,1.991-2.301,3.608-5.151,3.608c-2.845,0-5.153-1.612-5.153-3.608v2.257c1.071,1.2,2.979,2.001,5.153,2.001\n\t\t\tc3.359,0,6.083-1.903,6.083-4.259C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t\n\t\t\t<ellipse id=\"ellipse24\" opacity=\"0.25\" fill=\"#E6E6E6\" enable-background=\"new    \" cx=\"6.543\" cy=\"16.356\" rx=\"5.153\" ry=\"3.606\"/>\n\t\t\n\t\t\t<ellipse id=\"color_ellipse26\" opacity=\"0.25\" fill=\"#E60000\" enable-background=\"new    \" cx=\"6.543\" cy=\"16.356\" rx=\"5.153\" ry=\"3.606\"/>\n\t\t<polygon id=\"polygon28\" fill=\"#666666\" points=\"2.991,11.661 2.991,16.355 3.714,16.355 3.714,14.167 5.763,14.167 8.668,11.048 \n\t\t\t3.867,11.048 \t\t\"/>\n\t\t<polygon id=\"polygon30\" fill=\"#666666\" points=\"9.226,10.844 9.544,11.214 6.778,14.167 9.431,14.167 9.431,16.355 10.095,16.355 \n\t\t\t10.095,10.844 \t\t\"/>\n\t\t<path id=\"color_path32\" opacity=\"0.65\" fill=\"#E60000\" enable-background=\"new    \" d=\"M11.694,14.099V9.8\n\t\t\tc0-2.845-2.303-5.153-5.151-5.153C3.698,4.647,1.39,6.951,1.39,9.8v9.921c1.071,1.201,2.979,2.001,5.153,2.001\n\t\t\tc3.359,0,6.083-1.902,6.083-4.26v-1.107C12.626,15.525,12.281,14.754,11.694,14.099z\"/>\n\t\t<path id=\"path34\" opacity=\"0.5\" fill=\"#FFFFFF\" enable-background=\"new    \" d=\"M8.943,7.376l1.043-0.199\n\t\t\tC9.374,6.354,8.473,5.754,7.411,5.55l0.186,0.786C8.152,6.532,8.619,6.903,8.943,7.376z\"/>\n\t\t<path id=\"path36\" opacity=\"0.5\" fill=\"#FFFFFF\" enable-background=\"new    \" d=\"M1.948,19.132v1.104\n\t\t\tc0.472,0.385,1.042,0.71,1.677,0.957v-1.107C2.988,19.841,2.422,19.518,1.948,19.132z\"/>\n\t\t<path id=\"path38\" opacity=\"0.5\" fill=\"#FFFFFF\" enable-background=\"new    \" d=\"M9.44,19.338\n\t\t\tc-0.186,0.089-0.385,0.167-0.585,0.239c-0.042,0.015-0.086,0.03-0.13,0.043c-0.41,0.131-0.844,0.231-1.305,0.287\n\t\t\tc-0.054,0.007-0.11,0.015-0.164,0.015c-0.233,0.021-0.468,0.042-0.706,0.042c-0.108,0-0.223-0.012-0.343-0.018\n\t\t\tc-0.873-0.042-1.694-0.229-2.397-0.537v-6.098V9.803c0-1.069,0.616-1.984,1.507-2.435L5.302,7.33l-0.907-1.1\n\t\t\tC3.181,6.959,2.367,8.281,2.367,9.801v8.653c-0.036-0.035-0.224-0.224-0.349-0.384l-0.224,0.499\n\t\t\tc1.019,1.077,2.769,1.789,4.757,1.789c1.222,0,2.354-0.271,3.28-0.728l-0.383-0.298C9.44,19.338,9.44,19.338,9.44,19.338z\"/>\n\t</g>\n</g>\n</svg>\n"

FZP = '''<module><title>Example LED</title><author>Ada</author><properties><property name="license">CC BY-SA 3.0</property><property name="family">LED</property></properties><views><breadboardView><layers image="breadboard/led.svg"/></breadboardView></views><connectors><connector id="connector0" name="Cathode"/><connector id="connector1" name="Anode"/></connectors><spice><model>NEVER EXECUTED</model></spice></module>'''
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect id="body" width="10" height="10" fill="#cc0000"/></svg>'


def packed(files, compression=zipfile.ZIP_DEFLATED):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', compression=compression) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return data.getvalue()


class FritzingPartTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def archive(self, fzp=FZP, svg=SVG, image='svg.breadboard.led.svg', extra=None):
        return packed({'part.example.fzp': fzp, image: svg, **(extra or {})})

    def test_flat_archive_persists_metadata_and_sanitized_art(self):
        part = import_part(self.archive(extra={'LICENSE.txt': 'Credit Ada; CC BY-SA 3.0'}), self.root)
        self.assertRegex(part['id'], r'^[0-9a-f]{32}$')
        self.assertEqual(part['name'], 'Example LED')
        self.assertEqual(part['author'], 'Ada')
        self.assertEqual(part['license'], 'CC BY-SA 3.0')
        self.assertEqual(part['connectors'], ['Cathode', 'Anode'])
        self.assertEqual(part['support'], 'visual-only')
        self.assertEqual(part['properties']['family'], 'LED')
        self.assertIn('Credit Ada', part['attribution']['LICENSE.txt'])
        self.assertEqual(part['svgUrl'], '/api/visual-parts/' + part['id'] + '.svg')
        self.assertEqual(list_parts(self.root), [part])
        self.assertIn('#cc0000', svg_path(part['id'], self.root).read_text())
        self.assertEqual(len(list(self.root.iterdir())), 1)
        self.assertNotIn('model', part)

    def test_official_led_imports_unmodified_with_known_inert_doctype(self):
        files = {'part.LED-generic-3mm.fzp': OFFICIAL_FZP,
                 'svg.breadboard.LED-3mm-red-leg.svg': OFFICIAL_SVG,
                 'LICENSE.txt': 'Graphics and documentation: Fritzing; CC BY-SA 3.0 Unported. https://creativecommons.org/licenses/by-sa/3.0/'}
        part = import_part(packed(files), self.root)
        self.assertEqual(part['name'], 'Red LED - 3mm')
        self.assertEqual(part['author'], 'Stefan Hermann')
        self.assertEqual(part['connectors'], ['cathode', 'anode'])
        self.assertIn('CC BY-SA 3.0', part['attribution']['LICENSE.txt'])
        self.assertIn('connector0leg', svg_path(part['id'], self.root).read_text())
        self.assertNotIn('DOCTYPE', svg_path(part['id'], self.root).read_text())
        self.assertEqual(part['support'], 'visual-only')

    def test_slash_layout_and_nested_zip_layout(self):
        for name in ['breadboard/led.svg', 'bundle/breadboard/led.svg']:
            part = import_part(self.archive(image=name), self.root)
            self.assertTrue(svg_path(part['id'], self.root).is_file())

    def test_ambiguous_missing_or_duplicate_fzp_rejected(self):
        for data in [self.archive(extra={'breadboard/led.svg': SVG}), packed({'part.fzp': FZP}), self.archive(extra={'other.fzp': FZP}), packed({'led.svg': SVG})]:
            with self.subTest(data=data[:20]), self.assertRaises(ValueError):
                import_part(data, self.root)
        self.assertEqual(list_parts(self.root), [])

    def test_rejects_zip_traversal_absolute_paths_windows_and_symlinks(self):
        for name in ['../evil', '/tmp/evil', 'C:/evil', 'x\\evil', 'x/../../evil']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                import_part(self.archive(extra={name: 'x'}), self.root)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('part.fzp', FZP)
            info = zipfile.ZipInfo('svg.breadboard.led.svg')
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, 'target.svg')
        with self.assertRaises(ValueError):
            import_part(stream.getvalue(), self.root)

    def test_zip_limits_and_invalid_input(self):
        for data in [b'not a ZIP', b'x' * 1_000_001, self.archive(extra={str(i): '' for i in range(31)}), self.archive(extra={'bomb': b'a' * 3_000_001})]:
            with self.assertRaises(ValueError):
                import_part(data, self.root)
        self.assertEqual(list_parts(self.root), [])

    def test_dtd_entities_and_malformed_xml_rejected(self):
        declarations = ['<!DOCTYPE module [<!ENTITY steal SYSTEM "file:///etc/passwd">]>', '<!DOCTYPE svg SYSTEM "https://example.org/evil.dtd">']
        for declaration in declarations:
            for where in ['fzp', 'svg']:
                source = declaration + (FZP if where == 'fzp' else SVG)
                for encoding in ['utf-8', 'utf-16', 'utf-32']:
                    with self.subTest(where=where, encoding=encoding), self.assertRaises(ValueError):
                        import_part(self.archive(**{where: source.encode(encoding)}), self.root)
        with self.assertRaises(ValueError):
            import_part(self.archive(fzp='<module>'), self.root)
        with self.assertRaises(ValueError):
            import_part(self.archive(svg='<html/>'), self.root)

    def test_svg_allowlist_removes_active_content_and_keeps_gradients(self):
        malicious = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" onload="alert(1)"><script>alert(1)</script><foreignObject><p>HTML</p></foreignObject><image href="https://evil.test/pixel"/><style>@import 'https://evil.test/style';</style><defs><linearGradient id="red"><stop offset="0" style="stop-color:#f00;stop-opacity:0.5"/></linearGradient><linearGradient id="copy" xlink:href="#red"/></defs><rect id="body" fill="url(#red)" onclick="evil()" style="fill:url(#copy);stroke:#111;filter:url(https://evil.test/x);opacity:0.5;background:expression(alert(1))"/><path fill="url(https://evil.test/x)" d="M0 0 L1 1"/><use href="#body"/><animate attributeName="href" values="javascript:evil()"/></svg>'''
        part = import_part(self.archive(svg=malicious), self.root)
        text = svg_path(part['id'], self.root).read_text()
        tree = ET.fromstring(text)
        for forbidden in ['script', 'foreignObject', 'image', '<style', 'onload', 'onclick', 'https:', 'expression', 'animate', '<use']:
            self.assertNotIn(forbidden, text)
        self.assertIn('fill="url(#copy)"', text)
        self.assertIn('stop-color="#f00"', text)
        self.assertIn('href="#red"', text)
        self.assertIn('stroke="#111"', text)
        self.assertNotIn('style=', text)
        self.assertEqual(tree.tag, '{http://www.w3.org/2000/svg}svg')

    def test_css_obfuscation_and_foreign_namespaces_removed(self):
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:e="https://evil.test"><e:rect/><rect style="fill:u\\72l(https://evil.test/x);stroke:red" fill="url( /*x*/ https://evil.test/x)"/><rect style="fill:url('data:image/svg+xml,x');opacity:1"/></svg>'''
        part = import_part(self.archive(svg=svg), self.root)
        text = svg_path(part['id'], self.root).read_text()
        self.assertNotIn('evil', text)
        self.assertNotIn('data:', text)
        self.assertIn('stroke="red"', text)

    def test_inline_styles_become_presentation_attributes_with_css_precedence(self):
        for attributes in ['style="fill:red;stroke:blue" fill="green"', 'fill="green" style="fill:red;stroke:blue"', 'fill="green" style="fill:red !important;fill:blue"']:
            with self.subTest(attributes=attributes):
                part = import_part(self.archive(svg='<svg><rect ' + attributes + '/></svg>'), self.root)
                tree = ET.parse(svg_path(part['id'], self.root))
                rect = tree.getroot()[0]
                self.assertEqual(rect.get('fill'), 'red')
                self.assertNotIn('style', rect.attrib)

    def test_known_doctype_with_internal_subset_or_changed_url_still_rejected(self):
        declaration = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"'
        for suffix in [' [<!ENTITY boom "oops">]>', ' []>']:
            with self.assertRaisesRegex(ValueError, 'DTD'):
                import_part(self.archive(svg=declaration + suffix + SVG), self.root)
        with self.assertRaisesRegex(ValueError, 'DTD'):
            import_part(self.archive(svg=declaration.replace('www.w3.org', 'evil.test') + '>' + SVG), self.root)

    def test_strict_id_and_no_symlink_svg(self):
        for key in ['../secret', 'A' * 32, '0' * 31, '', None]:
            with self.assertRaises(ValueError):
                svg_path(key, self.root)
        with self.assertRaises(FileNotFoundError):
            svg_path('0' * 32, self.root)
        folder = self.root / ('1' * 32)
        folder.mkdir()
        (folder / 'part.svg').symlink_to('/etc/passwd')
        with self.assertRaises(FileNotFoundError):
            svg_path('1' * 32, self.root)

    def test_excessively_nested_svg_and_duplicate_zip_files_rejected(self):
        nested = '<svg>' + '<g>' * 130 + '</g>' * 130 + '</svg>'
        with self.assertRaisesRegex(ValueError, 'nesting'):
            import_part(self.archive(svg=nested), self.root)
        stream = io.BytesIO()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(stream, 'w') as archive:
                archive.writestr('part.fzp', FZP)
                archive.writestr('svg.breadboard.led.svg', SVG)
                archive.writestr('svg.breadboard.led.svg', SVG)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            import_part(stream.getvalue(), self.root)
