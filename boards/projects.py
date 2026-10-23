"""Explicit multi-device wiring; imported artwork never creates a model."""
import copy
import math

# This registry is the source of truth for the practical workspace's selectable models.
MODELS = {
 'lm35': {'kind':'analog','value':25,'range':[0,150],'unit':'°C'},
 'tmp36': {'kind':'analog','value':25,'range':[-40,125],'unit':'°C'},
 'ntc10k': {'kind':'analog','value':25,'range':[-20,100],'unit':'°C'},
 'potentiometer': {'kind':'analog','value':50,'range':[0,100],'unit':'%'},
 'light-divider': {'kind':'analog','value':50,'range':[0,100],'unit':'% normalized'},
 'joystick-axis': {'kind':'analog','value':50,'range':[0,100],'unit':'% one axis'},
 'button': {'kind':'digital','value':False}, 'pir': {'kind':'digital','value':False},
 'reed-switch': {'kind':'digital','value':False}, 'ir-obstacle': {'kind':'digital','value':False},
 'hcsr04': {'kind':'pulse','distanceCm':100,'range':[2,400],'unit':'cm'},
 'lm75': {'kind':'i2c','address':72,'temperature':25,'range':[-55,125],'unit':'°C'},
 'ds1621': {'kind':'i2c','address':72,'temperature':25,'range':[-55,125],'unit':'°C'},
 'bmp180': {'kind':'i2c','address':119,'temperature':25,'pressureHpa':1013.25,'range':[-55,85],'unit':'°C'},
 'bh1750': {'kind':'i2c','address':35,'lux':1000,'range':[0,100000],'unit':'lux'},
 'ads1115': {'kind':'i2c','address':72,'voltages':[1,2,0,0],'unit':'V'},
 'pcf8574': {'kind':'i2c','address':32,'inputs':255,'unit':'8-bit external input mask'},
 'mpu6050': {'kind':'i2c','address':104,'accelG':[0,0,1],'gyroDps':[0,0,0],'temperature':25,'range':[-40,85],'unit':'g / deg/s / °C'},
 'led': {'kind':'output','pin':13}, 'servo': {'kind':'output','pin':9}, 'buzzer': {'kind':'output','pin':9},
}

def number(v,lo,hi,label,integer=False):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi or (integer and int(v)!=v):
  raise ValueError(f'{label} must be {lo}–{hi}'+(' integer.' if integer else '.'))
 return v

def prepare_project(project):
 if not isinstance(project,dict) or project.get('version')!=1:raise ValueError('Project version must be 1.')
 if project.get('board') not in {'arduino-uno','arduino-nano'}:raise ValueError('Practical projects currently require Uno or classic Nano.')
 duration=number(project.get('durationMs',250),1,1000,'Duration')
 components=project.get('components')
 if not isinstance(components,list) or len(components)>32:raise ValueError('Project requires a list of at most 32 components.')
 result={'board':project['board'],'durationMs':duration,'sensors':[],'devices':[],'i2cDevices':[],'outputs':[]}
 claims,addresses,ids=set(),set(),set()
 def claim(pin):
  if pin in claims:raise ValueError('Wiring conflict on '+pin)
  claims.add(pin)
 for raw in components:
  if not isinstance(raw,dict):raise ValueError('Invalid component.')
  c=copy.deepcopy(raw);ident=c.pop('id',None);model=c.get('model')
  if not isinstance(ident,str) or not 1<=len(ident)<=64 or ident in ids:raise ValueError('Each component needs a unique ID.')
  ids.add(ident)
  if model not in MODELS:raise ValueError('No executable model for '+str(model))
  profile=MODELS[model];kind=profile['kind']
  if 'connected' in c and not isinstance(c['connected'],bool):raise ValueError('Connected must be boolean.')
  if kind=='i2c':
   c.setdefault('address',profile['address']);address=number(c['address'],8,119,'I2C address',True)
   valid=(address in [104,105] if model=='mpu6050' else address in [35,92] if model=='bh1750' else address==119 if model=='bmp180' else 72<=address<=75 if model=='ads1115' else 32<=address<=39 if model=='pcf8574' else 72<=address<=79)
   if not valid:raise ValueError('Unsupported I2C address for '+model)
   if address in addresses:raise ValueError('I2C address conflict: '+hex(address))
   addresses.add(address)
   if 'temperature' in profile:c['temperature']=number(c.get('temperature',25),*profile['range'],'Temperature')
   if model=='bh1750':c['lux']=number(c.get('lux',1000),0,100000,'Lux')
   if model=='bmp180':c['pressureHpa']=number(c.get('pressureHpa',1013.25),300,1100,'Pressure')
   if model=='pcf8574':c['inputs']=number(c.get('inputs',255),0,255,'Input mask',True)
   if model=='mpu6050':
    for key,bound in [('accelG',16),('gyroDps',2000)]:
     values=c.get(key,profile[key])
     if not isinstance(values,list) or len(values)!=3:raise ValueError(key+' requires a three-axis numeric vector.')
     c[key]=[number(x,-bound,bound,key) for x in values]
   if model=='ads1115':
    v=c.get('voltages',[1,2,0,0])
    if not isinstance(v,list) or len(v)!=4:raise ValueError('ADS1115 requires four voltages.')
    c['voltages']=[number(x,0,5,'ADS1115 voltage') for x in v]
   if c.get('changes'):raise ValueError('Scheduled changes are currently supported on analog and digital inputs only.')
   result['i2cDevices'].append(c)
  elif kind=='output':
   if c.get('connected') is False:continue
   c['pin']=number(c.get('pin',profile['pin']),2,13,'Output pin',True)
   result['outputs'].append({'id':ident,'model':model,'pin':c['pin']})
  else:
   if c.get('connected') is False:continue
   if kind=='pulse':
    for name,default in [('triggerPin',3),('echoPin',2)]:c[name]=number(c.get(name,default),2,13,name,True);claim('D'+str(c[name]))
    c['distanceCm']=number(c.get('distanceCm',100),2,400,'Distance')
   else:
    c['pin']=number(c.get('pin',0 if kind=='analog' else 2),0 if kind=='analog' else 2,5 if kind=='analog' else 13,'Pin',True)
    claim(('A' if kind=='analog' else 'D')+str(c['pin']))
    c.setdefault('value',profile['value'])
    if kind=='analog':number(c['value'],*profile['range'],'Input value')
    elif not isinstance(c['value'],bool):raise ValueError('Digital input value must be boolean.')
   changes=c.get('changes',[])
   if not isinstance(changes,list) or len(changes)>64:raise ValueError('At most 64 input changes per device.')
   last=-1
   for event in changes:
    if kind not in {'analog','digital'} or not isinstance(event,dict):raise ValueError('Changes require an analog/digital input.')
    at=number(event.get('atMs'),0,duration,'Stimulus time')
    if at<=last:raise ValueError('Stimulus times must increase strictly.')
    last=at
    if kind=='analog':number(event.get('value'),*profile['range'],'Stimulus value')
    elif not isinstance(event.get('value'),bool):raise ValueError('Digital stimulus must be boolean.')
   result['sensors' if kind=='analog' else 'devices'].append(c)
 if addresses and claims&{'A4','A5'}:raise ValueError('A4/A5 are reserved for the shared I2C bus.')
 for output in result['outputs']:
  if 'D'+str(output['pin']) in claims:raise ValueError('Output conflicts with externally driven input pin.')
 if len(result['sensors'])>6 or len(result['devices'])>8 or len(result['i2cDevices'])>16:raise ValueError('Project exceeds engine device limits.')
 return result
