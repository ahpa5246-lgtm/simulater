import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from boards.service import run_board, compile_sketch, board_catalogue
from boards.libraries import install_library, list_libraries

SKETCH='''#include <Arduino.h>
void setup(){ Serial.begin(9600); pinMode(13,OUTPUT); }
void loop(){ int value=analogRead(A0); digitalWrite(13,value>100); Serial.println(value); delay(10); }
'''

def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for name,content in files.items():z.writestr(name,content)
    return stream.getvalue()

class BoardTests(unittest.TestCase):
    def test_real_firmware_reads_changed_sensor_voltage(self):
        compiled=compile_sketch(SKETCH)
        low=run_board({'board':'arduino-uno','hex':compiled['hex'],'durationMs':60,'sensors':[{'model':'lm35','value':25,'pin':0}]})
        high=run_board({'board':'arduino-uno','hex':compiled['hex'],'durationMs':60,'sensors':[{'model':'lm35','value':100,'pin':0}]})
        self.assertIn('51',low['serial']);self.assertIn('204',high['serial'])
        self.assertFalse(low['pins']['D13']);self.assertTrue(high['pins']['D13'])
        self.assertGreater(high['cycles'],900000)
    def test_wire_library_reads_i2c_sensor(self):
        source='#include <Wire.h>\n#include <Arduino.h>\nvoid setup(){Serial.begin(9600);Wire.begin();}\nvoid loop(){Wire.beginTransmission(0x48);Wire.write(0);Wire.endTransmission();Wire.requestFrom(0x48,2);if(Wire.available()==2){int raw=(Wire.read()<<8)|Wire.read();Serial.println(raw>>7);}delay(10);}'
        firmware=compile_sketch(source)['hex']
        result=run_board({'board':'arduino-uno','hex':firmware,'durationMs':80,'i2cTemperature':30})
        self.assertIn('60',result['serial']);self.assertTrue(any(row['event']=='READ' for row in result['bus']))

    def test_unknown_board_is_not_silently_emulated(self):
        with self.assertRaisesRegex(ValueError,'supported'):run_board({'board':'esp32','hex':':00000001FF','durationMs':10})
    def test_bad_hex_checksum_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'checksum'):run_board({'board':'arduino-uno','hex':':020000000000FF\n:00000001FF','durationMs':10})
    def test_sensor_range_is_validated(self):
        firmware=compile_sketch(SKETCH)['hex']
        with self.assertRaises(ValueError):run_board({'board':'arduino-uno','hex':firmware,'sensors':[{'model':'lm35','value':999,'pin':0}]})
    def test_library_install_and_compile(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            packed=archive({'ExampleGain/library.properties':'name=ExampleGain\nversion=1.0.0\nlicense=MIT\n','ExampleGain/src/Gain.h':'#pragma once\ninline int gain(int x){return x*2;}\n'})
            installed=install_library(packed,root);self.assertEqual(installed['name'],'ExampleGain')
            self.assertEqual(len(list_libraries(root)),1)
            result=compile_sketch('#include <Gain.h>\n'+SKETCH.replace('analogRead(A0)','gain(analogRead(A0))'),root)
            self.assertTrue(result['hex'].startswith(':'))
    def test_rejects_excessive_library_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            files={'Large/library.properties':'name=Large\nversion=1.0\n','Large/src/Large.h':'// header'}
            files.update({f'Large/src/file{i}.cpp':'// source' for i in range(105)})
            install_library(archive(files),root)
            with self.assertRaisesRegex(ValueError,'100 source'):compile_sketch('#include <Large.h>\n'+SKETCH,root)

    def test_blocks_assembler_host_file_reads(self):
        source=r'asm(".in" "cbin \"/etc/hostname\"\n");'+'\n'+SKETCH
        with self.assertRaisesRegex(ValueError,'file-read'):compile_sketch(source)
    def test_blocks_foreign_preprocessor_includes(self):
        with self.assertRaisesRegex(ValueError,'include|Preprocess'):compile_sketch('#include "/etc/hostname"\n'+SKETCH)

    def test_nano_has_its_own_board_definition(self):
        source='#ifndef ARDUINO_AVR_NANO\n#error wrong board definition\n#endif\n'+SKETCH
        self.assertTrue(compile_sketch(source,board='arduino-nano')['hex'].startswith(':'))

    def test_rejects_zip_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):install_library(archive({'../../evil.h':'x'}),Path(folder))
    def test_existing_library_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            packed=archive({'Safe/library.properties':'name=Safe\nversion=1.0\n','Safe/src/Safe.h':'// source'})
            install_library(packed,Path(folder))
            with self.assertRaisesRegex(ValueError,'already'):install_library(packed,Path(folder))
    def test_catalogue_distinguishes_pi_from_pico(self):
        ids={b['id'] for b in board_catalogue()}
        self.assertIn('raspberry-pi-pico',ids);self.assertIn('raspberry-pi-4',ids)

if __name__=='__main__':unittest.main()
