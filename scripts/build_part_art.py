"""Generate original CC0 component illustrations, with explicit connector coordinates."""
from pathlib import Path
import json
from html import escape
OUT=Path(__file__).resolve().parents[1]/'web/parts'
OUT.mkdir(exist_ok=True)
parts=[]
def rect(x,y,w,h,fill,rx=3,stroke='none'):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def circle(x,y,r,fill,stroke='none'):
 return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}"/>'
def text(x,y,t,size=12,fill='#eef5f7'):
 return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-family="sans-serif" text-anchor="middle">{escape(t)}</text>'
def path(d,stroke='#a6acb0',width=3,fill='none'):
 return f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}" stroke-linecap="round"/>'
def chip(x,y,w,h):
 s=rect(x,y,w,h,'#24292d',2,'#101518')
 for i in range(8):
  px=x+4+i*(w-8)/7;s+=rect(px,y-5,2,5,'#b5bdc2',0)+rect(px,y+h,2,5,'#b5bdc2',0)
 return s+circle(x+5,y+5,2,'#7d8589')
def save(id,name,group,body,pins=(),support='modeled',view='0 0 240 160'):
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" role="img"><title>{escape(name)}</title><defs><linearGradient id="metal"><stop stop-color="#8c959d"/><stop offset=".4" stop-color="#f2f4f5"/><stop offset="1" stop-color="#8c969e"/></linearGradient><radialGradient id="cone"><stop stop-color="#3a4249"/><stop offset=".65" stop-color="#242c33"/><stop offset=".8" stop-color="#a5b1b8"/><stop offset="1" stop-color="#d7dfe4"/></radialGradient></defs>{body}</svg>'
 (OUT/f'{id}.svg').write_text(svg)
 parts.append(dict(id=id,name=name,group=group,support=support,pins=[dict(name=n,x=x,y=y) for n,x,y in pins]))
def sensor(id,name,body,labels=('VCC','OUT','GND')):
 xs={2:[80,160],3:[60,120,180],4:[45,95,145,195]}[len(labels)]
 pins=list(zip(labels,xs,[148]*len(xs)))
 for label,x,y in pins:body+=rect(x-3,126,6,23,'url(#metal)',0)+circle(x,148,3,'#d2b460')+text(x,122,label,9,'#3c555f')
 save(id,name,'Sensors & inputs',body,pins)
sensor('lm35','LM35',rect(85,36,70,60,'#252b30',12)+path('M85 55H155','#555e65',2)+text(120,69,'LM35',14))
sensor('tmp36','TMP36',rect(85,36,70,60,'#252b30',12)+path('M85 55H155','#555e65',2)+text(120,69,'TMP36',13))
sensor('bmp180','BMP180 barometer',rect(55,20,130,92,'#6a3e88',5)+chip(94,46,52,36)+text(120,36,'BMP180',12),('SDA','SCL','VCC','GND'))
sensor('ds1621','DS1621 register model',rect(55,20,130,92,'#286b99',5)+chip(94,46,52,36)+text(120,36,'DS1621',12),('SDA','SCL','VCC','GND'))
sensor('lm75','LM75 module',rect(55,20,130,92,'#286b99',5)+chip(94,46,52,36)+text(120,36,'LM75',12)+circle(66,31,5,'#d3bc80')+rect(68,57,12,22,'#c3ac7b'),('SDA','SCL','VCC','GND'))
sensor('hcsr04','HC-SR04 ultrasonic',rect(15,24,210,90,'#236f9e',5)+circle(62,70,37,'url(#cone)')+circle(178,70,37,'url(#cone)')+text(120,34,'HC-SR04',10)+chip(100,62,38,20),('VCC','TRIG','ECHO','GND'))
sensor('potentiometer','Rotary potentiometer',circle(120,70,44,'#577784')+circle(120,70,30,'#c0c8cc')+circle(120,70,19,'url(#metal)')+path('M120 70L133 45','#303b43',5))
sensor('light-divider','Light-dependent resistor divider',rect(52,28,136,84,'#326f5a',4)+circle(95,64,28,'#d4ab71')+path('M78 49H110L80 58H110L80 67H110L80 77H110','#92512e',3)+rect(143,46,16,37,'#d9c5a2')+path('M143 55H159 M143 65H159','#8b522d',3))
sensor('ntc10k','NTC 10k thermistor',path('M100 86V105H60V126 M140 86V105H180V126','#aaa49b',4)+circle(120,62,30,'#b16634')+text(120,67,'103',16),('VCC','A0','GND'))
sensor('joystick-axis','Joystick module · one axis',rect(52,22,136,92,'#235d72')+rect(66,35,108,65,'#9aa8ae',6)+circle(120,64,36,'#292e35')+circle(120,64,24,'#424952')+path('M109 54Q120 44 130 54','#68717a',3),('VCC','VRx','GND'))
sensor('button','Tactile pushbutton',rect(64,32,112,76,'#b7c1c7',4)+rect(75,42,90,56,'#282e34')+circle(120,70,23,'#3b4248')+circle(120,70,16,'#5c656d'),('VCC','OUT','GND'))
sensor('pir','PIR motion module',rect(55,20,130,94,'#326c55')+circle(120,65,44,'#e3e9e5')+''.join(path(f'M{80+i*13} 40Q120 90 {80+i*13} 95','#c4d0c9',1) for i in range(7))+path('M78 53H162 M78 68H162 M87 83H153','#c4d0c9',1))
sensor('reed-switch','Reed contact module',rect(50,22,140,90,'#356b95')+rect(65,48,110,22,'#d1e6df',10,'#8faaa1')+path('M64 59H112 M128 59H177','#707d80',3)+path('M112 59L128 55','#8b9a98',2))
sensor('ir-obstacle','IR obstacle module',rect(50,20,140,94,'#28668a')+circle(88,51,20,'#e0e6e1')+circle(143,51,20,'#222b35')+chip(83,81,70,20)+rect(158,80,20,22,'#276aa8')+circle(168,90,6,'#bec6c3'))
# Two-terminal assets keep endpoints at (0,40) and (120,40), preserving circuit connectivity.
lead=path('M0 40H120','#9aabb3',4)
save('resistor','Resistor','Circuit components',lead+rect(25,25,70,30,'#d8bc8b',10)+''.join(rect(x,26,5,28,col,0) for x,col in [(39,'#855027'),(50,'#1d252b'),(61,'#c74738'),(81,'#b89a47')]),[('1',0,40),('2',120,40)],view='0 0 120 80')
save('capacitor','Capacitor','Circuit components',lead+rect(35,10,50,60,'#215b87',12)+rect(72,16,8,48,'#afc6cf',1)+text(58,44,'C',20),[('+',0,40),('−',120,40)],view='0 0 120 80')
save('inductor','Inductor','Circuit components',lead+rect(28,23,64,34,'#414f54',5)+''.join(path(f'M{x} 25Q{x-10} 40 {x} 55','#bc753c',6) for x in range(35,90,9)),[('1',0,40),('2',120,40)],view='0 0 120 80')
save('diode','Silicon diode','Circuit components',lead+rect(30,27,60,26,'#252c33',5)+rect(76,28,8,24,'#bdc8cd',0)+text(54,45,'D',13),[('A',0,40),('K',120,40)],view='0 0 120 80')
for id,name in [('dc-source','DC voltage source'),('ac-source','AC voltage source')]:
 save(id,name,'Circuit components',lead+rect(29,7,62,66,'#dee6e8',7,'#849aa5')+rect(36,14,48,22,'#213b42',3)+text(60,30,'~' if id=='ac-source' else 'DC',14,'#73d7c7')+circle(46,55,6,'#d55a4d')+circle(74,55,6,'#35414b'),[('+',0,40),('−',120,40)],view='0 0 120 80')
for id,name,state in [('arduino-uno','Arduino Uno R3','modeled'),('arduino-nano','Arduino Nano classic','modeled'),('raspberry-pi-pico','Raspberry Pi Pico','experimental'),('raspberry-pi-4','Raspberry Pi 4 / 5 family','visual only'),('esp32','ESP32 family','visual only'),('stm32','STM32 family','visual only'),('pic','PIC / dsPIC family','visual only')]:
 uno=id=='arduino-uno';compact=id in ('arduino-nano','raspberry-pi-pico');y0=75 if compact else 28;y1=175 if compact else 222
 body=rect(42,y0-15,326,y1-y0+30,'#178b96' if 'arduino' in id else '#27795a',8,'#315f65')
 body+=rect(25,100,53,47,'url(#metal)',4)+rect(29,109,25,28,'#626e75',2)+chip(167,98,100,53)+text(217,123,'RP2040' if 'pico' in id else 'ATmega328P' if 'arduino' in id else id.upper(),10)
 body+=text(206,y0+42,name,17)+text(217,140,'MINA • ILLUSTRATION',7,'#b5c9ca')
 for x,y in [(53,y0-3),(356,y0-3),(53,y1+3),(356,y1+3)]:body+=circle(x,y,5,'#c4ac6f')+circle(x,y,2,'#e9f0ee')
 pins=[]
 for i in range(14):
  x=90+i*19;n='GP'+str(i) if 'pico' in id else 'D'+str(13-i);pins.append((n,x,y0));body+=rect(x-6,y0-6,12,12,'#212d32',1)+circle(x,y0,2,'#bea86d')+text(x,y0+21,n,6)
 for i,n in enumerate(['VBUS','GND','GP26','GP27','GP28','3V3','VSYS','RUN'] if 'pico' in id else ['5V','GND','A0','A1','A2','A3','A4','A5']):
  x=90+i*34;pins.append((n,x,y1));body+=rect(x-6,y1-6,12,12,'#212d32',1)+circle(x,y1,2,'#bea86d')+text(x,y1-12,n,7)
 body+=rect(94,103,20,29,'#b9b8a5')+rect(94,151,22,14,'#222b32')+circle(139,160,11,'url(#metal)')+rect(311,115,12,5,'#c2ce75')
 if id=='esp32':
  body=rect(80,45,240,160,'#26313a',8)+rect(140,70,130,95,'url(#metal)',4)+text(205,120,'ESP32',20,'#39464d')+path('M100 60H123V75H101V90H124V105H102','#c0ad73',4)+rect(280,105,32,34,'url(#metal)')
 elif id=='stm32':
  body=rect(40,76,320,100,'#2869a0',4)+chip(165,97,63,60)+text(197,135,'STM32',12)+rect(35,100,40,38,'url(#metal)')+rect(276,100,22,22,'#eed268')+rect(309,100,22,22,'#eed268')
 elif id=='pic':
  body=rect(45,35,315,180,'#355c46',5)+chip(125,100,160,55)+text(205,130,'PIC / dsPIC',15)+rect(70,80,35,35,'#3c6a96')+circle(91,165,14,'url(#metal)')
 elif id=='raspberry-pi-4':
  body=rect(48,25,310,200,'#2d844c',10)+chip(153,87,64,64)+text(185,125,'SoC',15)+rect(273,43,75,50,'url(#metal)')+rect(273,102,75,50,'url(#metal)')+rect(270,163,80,50,'url(#metal)')+rect(70,36,156,18,'#222c2c')+''.join(circle(76+i*8,45,2,'#c8aa65') for i in range(19))+rect(45,172,42,25,'url(#metal)')
 if state=='visual only':pins=[]
 save(id,name,'Boards',body,pins,state,'0 0 400 250')
save('led','Onboard LED','Outputs',path('M95 90V145 M145 90V145','#a6acb0',5)+rect(85,48,70,58,'#b2c55a',25)+rect(78,97,84,12,'#77883c')+path('M101 60V85','#dae9a0',4),[('A',95,145),('K',145,145)],'GPIO output')
save('servo','Servo-style PWM signal','Outputs',rect(55,55,135,66,'#2879b1',7)+rect(70,36,50,24,'#265a84')+circle(95,37,17,'#d7dce0')+rect(65,29,106,15,'#e6ebed',7)+circle(95,36,5,'#78868e')+path('M190 85H220V145','#c95847',4),(),'Signal only · no mechanics')
save('buzzer','Buzzer tone output','Outputs',rect(66,52,108,62,'#212a32',16)+circle(120,52,54,'#303a42')+circle(120,52,12,'#141c23')+path('M86 114V145 M154 114V145','#abb7ba',5),(),'GPIO tone · no audio synthesis')
# Instrument illustrations represent existing panels, not extra hardware engines.
for id,name,screen in [('serial-monitor','Serial monitor','UART >_'),('logic-analyser','Logic analyser','GPIO'),('waveform-viewer','Waveform viewer','V(t)'),('library-manager','Library manager','ZIP / C++'),('firmware-studio','Firmware studio','HEX / UF2')]:
 body=rect(30,15,180,116,'#263d48',10)+rect(41,27,158,81,'#e1efec',5)+rect(96,132,48,9,'#8199a2')+rect(74,142,92,7,'#b2c4ca')+text(120,54,screen,17,'#326c72')
 body+=path('M54 88H75V70H95V88H116V70H137V88H165','#329f91',3) if id=='logic-analyser' else path('M54 87Q70 54 88 84T124 80T164 84','#329f91',3)
 save(id,name,'Tools',body,(), 'existing tool')
(OUT/'catalog.json').write_text(json.dumps(parts,indent=2)+'\n')
print(f'Generated {len(parts)} original illustrations')
