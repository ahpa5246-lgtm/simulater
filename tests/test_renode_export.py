import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('renode_export',Path('scripts/export-renode.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class RenodeExport(unittest.TestCase):
 def test_elf_guard_and_profile_export(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'app.elf';p.write_bytes(b'bad')
   with self.assertRaises(ValueError):module.script(p)
   data=bytearray(52);data[:7]=b'\x7fELF\x01\x01\x01';data[18:20]=(40).to_bytes(2,'little');p.write_bytes(data);s=module.script(p);self.assertIn('stm32f103.repl',s);self.assertIn(str(p),s);self.assertTrue(s.endswith('start\n'))
   bad=Path(folder)/'bad;name.elf';bad.write_bytes(data)
   with self.assertRaises(ValueError):module.script(bad)
