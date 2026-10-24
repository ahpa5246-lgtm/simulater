"""Practical project execution and honest artwork capability reporting."""
import hashlib
import json
import re
from pathlib import Path
from .projects import MODELS, prepare_project
from .service import compile_sketch,run_board
from analog_parts import PARTS

ROOT=Path(__file__).resolve().parents[1]

def run_project(request):
 if not isinstance(request,dict):raise ValueError('Invalid project execution request.')
 project=request.get('project');config=prepare_project(project)
 if 'hex' in request:
  config['hex']=request['hex']
 else:
  config['hex']=compile_sketch(request.get('source'),board=config['board'])['hex']
 result=run_board(config)
 outputs=[]
 for c in config['outputs']:
  pin='D'+str(c['pin']);measurement=result['instruments'].get(pin,{})
  output={**c,'pinName':pin,'high':result['pins'][pin],'measurement':measurement,'scope':'GPIO/pulse-driven ideal output indicator'}
  if c['model']=='servo':
   width=measurement.get('highUs');hz=measurement.get('frequencyHz')
   valid=isinstance(width,(int,float)) and isinstance(hz,(int,float)) and 500<=width<=2500 and 40<=hz<=60
   output['commandDegrees']=max(0,min(180,(width-1000)*.18)) if valid else None
   output['scope']='Pulse command mapping only; no shaft dynamics, torque or load model'
  outputs.append(output)
 result['outputs']=outputs
 result['evidence']['projectSha256']=hashlib.sha256(json.dumps(project,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 result['evidence']['projectDeviceCount']=len(project['components'])
 return result

def capabilities():
 records=[]
 for file,key in [('web/vendor/components/catalog.json','parts'),('web/vendor/wokwi-catalog.json',None),('web/parts/catalog.json',None)]:
  value=json.loads((ROOT/file).read_text());items=value[key] if key else value
  for p in items:
   ident=p.get('id',p.get('tag'));name=p['name'];matches=[]
   for chip in ['lm35','tmp36','lm75','ds1621','bmp180','bh1750','ads1115','pcf8574','mpu6050']:
    if re.search(r'(?<![a-z0-9])'+chip+r'(?![a-z0-9])',name,re.I):matches.append(chip)
   if ident in MODELS:matches.append(ident)
   aliases={'wokwi-hc-sr04':'hcsr04','wokwi-pushbutton':'button','wokwi-pushbutton-6mm':'button','wokwi-potentiometer':'potentiometer','wokwi-analog-joystick':'joystick-axis','wokwi-pir-motion-sensor':'pir','wokwi-ntc-temperature-sensor':'ntc10k','wokwi-led':'led','wokwi-servo':'servo','wokwi-buzzer':'buzzer'}
   if ident in aliases:matches.append(aliases[ident])
   matches=list(dict.fromkeys(matches))
   boards={'arduino-uno':'arduino-uno','arduino-nano':'arduino-nano','wokwi-arduino-uno':'arduino-uno','wokwi-arduino-nano':'arduino-nano','raspberry-pi-pico':'raspberry-pi-pico','wokwi-pi-pico':'raspberry-pi-pico'}
   analog={'resistor':'R','wokwi-resistor':'R','capacitor':'C','inductor':'L','diode':'D','dc-source':'V DC','ac-source':'V AC'}
   tools={'serial-monitor','logic-analyser','waveform-viewer','library-manager','firmware-studio'}
   target=boards.get(ident)
   if target:status='experimental-board' if target=='raspberry-pi-pico' else 'executable-board';detail='AVR firmware execution' if status=='executable-board' else 'Experimental RP2040 subset; use Boards & sensors'
   elif ident in analog:status='analog-solver';detail='ngspice '+analog[ident]+' model in Analog circuits'
   elif ident in tools:status='working-tool';detail='Available in the circuit or board workspace'
   elif matches:status='behavioral-model-available';detail='Use the listed model in a project; module wiring/power details require review.'
   else:status='no-model';detail='Artwork only; excluded from executable component picker.'
   records.append({'id':ident,'name':name,'catalogue':file,'models':matches,'boardTarget':target,'status':status,'detail':detail})
 return {'models':MODELS,'analogParts':PARTS,'records':records,'scope':'Explicit behavioral model support. Matching a chip name does not validate an entire breakout board. No general mixed-signal co-simulation.'}
