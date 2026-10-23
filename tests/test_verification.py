import unittest
from boards.verification import verify_models
class VerificationTests(unittest.TestCase):
    def test_report_is_backed_by_executed_firmware_and_reference_measurements(self):
        report=verify_models()
        self.assertGreaterEqual(len(report['cases']),10)
        self.assertEqual(report['failed'],0)
        self.assertEqual(report['passed'],len(report['cases']))
        for case in report['cases']:
            self.assertEqual(len(case['firmwareSha256']),64)
            self.assertGreater(case['cycles'],0)
            self.assertIn('measured',case);self.assertIn('expected',case)
        self.assertIn('not physical',report['scope'])
if __name__=='__main__':unittest.main()
