import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from boards import arduino_cli


class ArduinoCliTests(unittest.TestCase):
    def test_missing_executable_diagnostic(self):
        with patch.dict(os.environ, {'ARDUINO_CLI_BIN': '/nonexistent/arduino-cli'}):
            result = arduino_cli.status()
        self.assertFalse(result['available'])
        self.assertFalse(result['ok'])

    def test_validation_before_process(self):
        with patch.object(arduino_cli, '_run') as run:
            for name, version in [('--git-url', '1.2.3'), ('https://evil/a', '1.2.3'), ('Servo', 'latest'), ('Servo@x', '1.2.3'), ('Servo', '1.2.3;id')]:
                with self.assertRaises(ValueError):
                    arduino_cli.install_library(name, version)
            for query in ['--help', 'x; touch file', '../library', '', 'x\nname']:
                with self.assertRaises(ValueError):
                    arduino_cli.search_libraries(query)
            run.assert_not_called()

    def test_install_exact_args_and_no_implicit_dependencies(self):
        with patch.object(arduino_cli, '_run', return_value={}) as run:
            arduino_cli.install_library('Adafruit BusIO', '1.17.0')
        self.assertEqual(run.call_args.args[0], ['lib', 'install', '--no-deps', '--no-overwrite', 'Adafruit BusIO@1.17.0'])

    def test_compile_keeps_existing_policy(self):
        with patch('boards.service.compile_sketch', return_value={'hex': 'test'}) as compile_source:
            self.assertEqual(arduino_cli.compile_sketch('void setup(){}', 'arduino-nano'), {'hex': 'test'})
            compile_source.assert_called_once_with('void setup(){}', board='arduino-nano')
            with self.assertRaises(ValueError):
                arduino_cli.compile_sketch('source', 'esp32')

    def fake_cli(self, folder, body):
        binary = Path(folder) / 'fake-cli'
        binary.write_text(f'#!{sys.executable}\n' + body)
        binary.chmod(0o700)
        return binary

    def test_real_subprocess_boundary_config_and_cleanup(self):
        # Executable fixture, not an Arduino CLI integration test.
        with tempfile.TemporaryDirectory() as folder:
            binary = self.fake_cli(folder, 'import json,sys,os\nfrom pathlib import Path\np=Path(sys.argv[2])\nprint(json.dumps({"args":sys.argv[3:],"config":json.loads(p.read_text()),"cwd":os.getcwd(),"override":os.getenv("ARDUINO_DIRECTORIES_USER")}))\n')
            state = Path(folder) / 'state'
            with patch.dict(os.environ, {'ARDUINO_CLI_BIN': str(binary), 'ARDUINO_DIRECTORIES_USER': '/unwanted'}), patch.object(arduino_cli.subprocess, 'Popen', wraps=arduino_cli.subprocess.Popen) as popen:
                result = arduino_cli.search_libraries('Servo Motor', state)
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['args'], ['--json', '--no-color', 'lib', 'search', 'Servo Motor'])
            self.assertIsNone(result['data']['override'])
            self.assertEqual(result['data']['config']['directories']['user'], str(state / 'user'))
            self.assertFalse(popen.call_args.kwargs['shell'])
            self.assertFalse(Path(result['data']['cwd']).exists())
            self.assertEqual(list((state / 'tasks').iterdir()), [])

    def test_timeout_and_output_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = self.fake_cli(folder, 'import time\ntime.sleep(3)\n')
            with patch.dict(os.environ, {'ARDUINO_CLI_BIN': str(binary)}):
                result = arduino_cli._run(['version'], Path(folder) / 'state', timeout=.05)
            self.assertFalse(result['ok'])
            self.assertIn('timeout', result['diagnostic'])
            binary = self.fake_cli(folder, 'print("x"*100000)\n')
            with patch.dict(os.environ, {'ARDUINO_CLI_BIN': str(binary)}), patch.object(arduino_cli, 'OUTPUT_LIMIT', 1024):
                result = arduino_cli.status(Path(folder) / 'state')
            self.assertFalse(result['ok'])
            self.assertIn('output limit', result['diagnostic'])
            self.assertLessEqual(len(result.get('output', '')), 1024)

    @unittest.skipUnless(hasattr(os, 'fork'), 'POSIX fork regression')
    def test_timeout_kills_children_holding_pipes_even_after_parent_exits(self):
        for parent_exits in (False, True):
            with self.subTest(parent_exits=parent_exits), tempfile.TemporaryDirectory() as folder:
                body = 'import os,time\nchild=os.fork()\nif child == 0:\n time.sleep(1.5)\n os._exit(0)\n'
                body += 'os._exit(0)\n' if parent_exits else 'time.sleep(1.5)\n'
                binary = self.fake_cli(folder, body)
                with patch.dict(os.environ, {'ARDUINO_CLI_BIN': str(binary)}):
                    started = time.monotonic()
                    result = arduino_cli._run(['version'], Path(folder) / 'state', timeout=.05)
                    elapsed = time.monotonic() - started
                self.assertLess(elapsed, 1.0)
                self.assertFalse(result['ok'])
                self.assertIn('timeout', result['diagnostic'])
                self.assertEqual(list((Path(folder) / 'state/tasks').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
