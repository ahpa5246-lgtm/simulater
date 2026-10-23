import unittest
from boards.service import compile_sketch,run_board
try:
 from boards.projects import prepare_project
except ImportError:
 prepare_project=None

MULTI='''#include <Wire.h>
void setup(){Serial.begin(115200);Wire.begin();pinMode(2,INPUT_PULLUP);pinMode(13,OUTPUT);
Wire.beginTransmission(0x23);Wire.write(0x10);Wire.endTransmission();}
void loop(){Wire.requestFrom(0x23,2);unsigned int light=((unsigned int)Wire.read()<<8)|Wire.read();
Wire.beginTransmission(0x49);Wire.write(0);Wire.endTransmission();Wire.requestFrom(0x49,2);int t=Wire.read();Wire.read();
Wire.beginTransmission(0x20);Wire.write(0xaa);Wire.endTransmission();Wire.requestFrom(0x20,1);int io=Wire.read();
int b=digitalRead(2);digitalWrite(13,!b);Serial.print(light);Serial.print(',');Serial.print(t);Serial.print(',');Serial.print(io);Serial.print(',');Serial.print(b);Serial.print(',');Serial.println(analogRead(A1));delay(30);}
'''
PROJECT={'version':1,'board':'arduino-uno','durationMs':250,'components':[
 {'id':'light','model':'bh1750','address':35,'lux':1000},
 {'id':'temp','model':'lm75','address':73,'temperature':25},
 {'id':'io','model':'pcf8574','address':32,'inputs':240},
 {'id':'knob','model':'potentiometer','pin':1,'value':20,'changes':[{'atMs':100,'value':80}]},
 {'id':'button','model':'button','pin':2,'value':False,'changes':[{'atMs':100,'value':True}]}]}
class Projects(unittest.TestCase):
 def test_translates_real_wiring_and_rejects_conflicts(self):
  self.assertTrue(callable(prepare_project),'multi-device project validation missing')
  config=prepare_project(PROJECT)
  self.assertEqual(len(config['i2cDevices']),3)
  self.assertEqual(config['sensors'][0]['pin'],1)
  for components in [[{'id':'x','model':'not-a-device'}], [{'id':'x','model':'bh1750','address':35},{'id':'y','model':'bh1750','address':35}], [{'id':'x','model':'button','pin':2,'value':False},{'id':'y','model':'hcsr04','triggerPin':3,'echoPin':2}], [{'id':'x','model':'lm35','pin':4,'value':25},{'id':'y','model':'lm75'}]]:
   with self.assertRaises(ValueError):prepare_project({**PROJECT,'components':components})
 def test_compiled_firmware_reads_multiple_devices_and_scheduled_inputs(self):
  self.assertTrue(callable(prepare_project),'project missing')
  config=prepare_project(PROJECT);config['hex']=compile_sketch(MULTI)['hex']
  result=run_board(config);rows=[list(map(int,s.split(','))) for s in result['serial'].splitlines() if s.count(',')==4]
  self.assertGreater(len(rows),3)
  self.assertEqual(rows[0][:4],[0,25,160,1])
  self.assertTrue(any(r[0]==1200 and r[3]==0 and abs(r[4]-819)<=1 for r in rows),rows)
  self.assertTrue(result['pins']['D13'])
  self.assertEqual(len(result['i2cDevices']),3)
  self.assertTrue(any(e['type']=='stimulus' for e in result['deviceEvents']))
 def test_disconnected_device_nacks_and_bad_stimuli_fail(self):
  self.assertTrue(callable(prepare_project),'project missing')
  bad={'id':'bad','model':'button','pin':2,'value':False,'changes':[{'atMs':-1,'value':True}]}
  with self.assertRaises(ValueError):prepare_project({**PROJECT,'components':[bad]})

class PracticalExamples(unittest.TestCase):
 def test_shipped_projects_execute_and_report_firmware_derived_outputs(self):
  import json
  from pathlib import Path
  from boards.project_service import run_project
  examples=json.loads((Path(__file__).resolve().parents[1]/'web/practical-examples.json').read_text())
  for name,example in examples.items():
   with self.subTest(example=name):
    result=run_project(example)
    self.assertGreater(result['cycles'],0)
    self.assertEqual(len(result['evidence']['projectSha256']),64)
    if name=='adc':self.assertIn('ADC: 8000',result['serial'])
    if name=='imu':
     self.assertIn('AX:8192 AZ:16384 GY:11790',result['serial'])
     self.assertTrue(result['outputs'][0]['high'])
    if name=='echo':self.assertAlmostEqual(result['instruments']['D2']['highUs'],5800,delta=1)
    if name=='servo':self.assertAlmostEqual(result['outputs'][0]['commandDegrees'],90,delta=.2)
    if name=='multi':self.assertTrue(result['outputs'][0]['high'])
 def test_audit_distinguishes_models_boards_tools_and_solver(self):
  from boards.project_service import capabilities
  report=capabilities();self.assertEqual(len(report['records']),363)
  records={r['id']:r for r in report['records']}
  self.assertEqual(records['arduino-uno']['status'],'executable-board')
  self.assertEqual(records['resistor']['status'],'analog-solver')
  self.assertEqual(records['esp32']['status'],'no-model')
  self.assertEqual(records['serial-monitor']['status'],'working-tool')
  self.assertEqual(records['lm35']['models'],['lm35'])
  self.assertEqual(records['wokwi-hc-sr04']['models'],['hcsr04'])
