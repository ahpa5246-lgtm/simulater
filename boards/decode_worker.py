"""Restricted sigrok API-v3 trace runner for the bundled SPI/I2C/UART decoders.

GPL-3.0-or-later. Executes unchanged upstream Python decoder logic over captured
GPIO edges. This is a subset runtime, not libsigrokdecode's C runtime.
"""
import importlib.util,json,sys,types,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'third_party/sigrokdecode/decoders'
class EndCapture(Exception):pass
class TraceRuntime:
    def has_channel(self,index):return index in self.channel_map
    def register(self,kind,**kwargs):self.streams.append(kind);return len(self.streams)-1
    def put(self,start,end,stream,data):
        if self.streams[stream]==1 and len(self.annotations)<4000:self.annotations.append({'startCycle':start,'endCycle':min(end,self.end_cycle),'class':data[0],'text':data[1][0]})
        elif self.streams[stream]==2 and len(self.packets)<4000:self.packets.append({'startCycle':start,'endCycle':min(end,self.end_cycle),'data':data})
    def wait(self,conditions):
        conditions=conditions if isinstance(conditions,list) else [conditions]
        origin=self.samplenum
        targets=[origin+max(1,math.ceil(c['skip'])) for c in conditions if 'skip' in c]
        for attempt in range(24001):
            # Empty condition requests first/current sample, matching sigrok.
            if conditions==[{}] and not self.started:
                self.started=True;self.matched=[True];return tuple(self.states.get(self.channel_map.get(i),0) for i in range(self.channel_count))
            next_edge=self.events[self.position][0] if self.position<len(self.events) else self.end_cycle+1
            next_timer=min((t for t in targets if t>self.samplenum),default=self.end_cycle+1)
            sample=min(next_edge,next_timer)
            if sample>self.end_cycle:raise EndCapture()
            previous=self.states.copy();self.samplenum=sample
            while self.position<len(self.events) and self.events[self.position][0]==sample:
                _,pin,value=self.events[self.position];self.states[pin]=int(value);self.position+=1
            matched=[]
            for cond in conditions:
                good=True
                for key,rule in cond.items():
                    if key=='skip':good &= sample-origin>=max(1,math.ceil(rule));continue
                    pin=self.channel_map.get(key);old=previous.get(pin,0);new=self.states.get(pin,0)
                    good &= {'r':old==0 and new==1,'f':old==1 and new==0,'e':old!=new,'h':new==1,'l':new==0}.get(rule,False)
                matched.append(bool(good))
            if any(matched):self.started=True;self.matched=matched;return tuple(self.states.get(self.channel_map.get(i),0) for i in range(self.channel_count))
        raise ValueError('Decoder wait budget exceeded')
def decode(config):
    protocol=config.get('protocol');maps={'spi':['clk','miso','mosi','cs'],'i2c':['scl','sda'],'uart':['rx','tx']}
    if protocol not in maps:raise ValueError('Supported decoders: spi, i2c, uart')
    pins=config.get('pins',{});names=maps[protocol]
    if not isinstance(pins,dict) or any(k not in names or v not in ['D'+str(i) for i in range(14)] for k,v in pins.items()):raise ValueError('Invalid decoder pins')
    required={'spi':['clk'],'i2c':['scl','sda'],'uart':['rx']}[protocol]
    if any(n not in pins for n in required) or protocol=='spi' and not any(n in pins for n in ['mosi','miso']):raise ValueError('Required decoder channels missing')
    if len(set(pins.values()))!=len(pins):raise ValueError('Decoder channels must use different pins')
    edges=config.get('logic');end=config.get('capturedCycles')
    if not isinstance(edges,list) or len(edges)>12000 or type(end)!=int or not 0<end<=16000010:raise ValueError('Invalid capture')
    previous=-1
    for edge in edges:
        if not isinstance(edge,dict) or type(edge.get('cycle'))!=int or not previous<=edge['cycle']<=end or edge.get('pin') not in ['D'+str(i) for i in range(14)] or type(edge.get('value'))!=bool:raise ValueError('Invalid captured edge')
        previous=edge['cycle']
    stub=types.ModuleType('sigrokdecode');stub.Decoder=TraceRuntime;stub.OUTPUT_ANN=1;stub.OUTPUT_PYTHON=2;stub.OUTPUT_BINARY=3;stub.OUTPUT_META=4;stub.SRD_CONF_SAMPLERATE=10000
    sys.modules['sigrokdecode']=stub;sys.path.insert(0,str(ROOT))
    spec=importlib.util.spec_from_file_location('bundled_decoder',ROOT/protocol/'pd.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    decoder=module.Decoder();decoder.options={o['id']:o['default'] for o in decoder.options}
    options=config.get('options',{})
    if not isinstance(options,dict):raise ValueError('Invalid decoder options')
    allowed={'spi':{'cpol':(0,1),'cpha':(0,1)},'i2c':{},'uart':{}}[protocol]
    for key,value in options.items():
        if key not in allowed or type(value)!=int or value not in allowed[key]:raise ValueError('Unsupported decoder option')
        decoder.options[key]=value
    if protocol=='uart':
        baud=config.get('baud',9600)
        if type(baud)!=int or not 300<=baud<=1000000:raise ValueError('Invalid UART baud')
        decoder.options['baudrate']=baud
    decoder.channel_map={names.index(k):v for k,v in pins.items()};decoder.channel_count=len(names);decoder.streams=[];decoder.annotations=[];decoder.packets=[];decoder.events=[(e['cycle'],e['pin'],e['value']) for e in edges];decoder.states={};decoder.position=0;decoder.samplenum=0;decoder.end_cycle=end;decoder.started=False;decoder.matched=[]
    decoder.start();decoder.metadata(stub.SRD_CONF_SAMPLERATE,16000000)
    try:decoder.decode()
    except EndCapture:pass
    return {'protocol':protocol,'engine':'upstream sigrok Python decoder / Mina API-v3 subset runtime','pins':pins,'annotations':decoder.annotations,'packets':decoder.packets,'capturedCycles':end,'limitations':'Captured D0–D13 only; nominal 16 MHz; UART 8N1; no decoder stacking or C-runtime conformance claim.'}
if __name__=='__main__':
    try:print(json.dumps(decode(json.load(sys.stdin))))
    except Exception as e:print(json.dumps({'error':str(e)}));sys.exit(1)
