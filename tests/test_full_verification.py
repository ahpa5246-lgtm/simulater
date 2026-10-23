import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('full_verifier',ROOT/'scripts/verify-all.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)


class VerificationReportTests(unittest.TestCase):
    def test_fingerprint_detects_untracked_source_changes_but_not_generated_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'app.js').write_text('original');(root/'parts.json').write_text('[]')
            previous=verifier.ROOT;verifier.ROOT=root
            try:
                a=verifier.source_fingerprint();(root/'parts.json').write_text('[1]')
                b=verifier.source_fingerprint();self.assertNotEqual(a,b)
                (root/'screenshots').mkdir();(root/'screenshots/a.json').write_text('generated')
                self.assertEqual(b,verifier.source_fingerprint())
            finally:verifier.ROOT=previous

    def test_missing_optional_cli_is_reported_without_inventing_availability(self):
        report=verifier.dependency_snapshot({'ARDUINO_CLI_BIN':'/does/not/exist'})
        self.assertFalse(report['arduinoCli']['available'])
        self.assertTrue(report['arduinoCli']['optional'])
        self.assertIn('diagnostic',report['arduinoCli'])
