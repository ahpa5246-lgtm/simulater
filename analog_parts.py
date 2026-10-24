"""Trusted generic ngspice presets. Device equations are evaluated by ngspice.

Reference: https://ngspice.sourceforge.io/docs/ngspice-html-manual/manual.xhtml
These original educational parameter sets are not vendor device qualifications.
User-supplied model text, expressions, subcircuits and file paths are not accepted.
"""
import json
from pathlib import Path

PARTS = json.loads((Path(__file__).parent/'web/analog-parts.json').read_text())
BY_ID = {p['id']: p for p in PARTS}
DEFAULTS = dict(R='resistor', C='capacitor', L='inductor', V='v-dc', I='i-dc', D='silicon-diode')
KINDS = {p['type'] for p in PARTS}


def part_for(component):
    part = BY_ID.get(component.get('part', DEFAULTS.get(component.get('type'))))
    if not part or part['type'] != component.get('type'):
        raise ValueError('Unknown component profile or mismatched component type.')
    return part


def pins_for(component):
    return tuple(p['key'] for p in part_for(component)['pins'])


def spice_line(c):
    p=part_for(c);kind=c['type'];value=f'{c["value"]:.12g}'
    nodes=' '.join(c[k].lower() for k in pins_for(c))
    if kind in {'V','I'}:
        wave=c.get('wave',p.get('wave','dc'));f=c.get('frequency',1000)
        if wave=='sine':value=f'DC 0 SIN(0 {value} {f:.12g})'
        elif wave=='pulse':value=f'DC 0 PULSE(0 {value} 0 1n 1n {0.5/f:.12g} {1/f:.12g})'
        else:value='DC '+value
    elif kind=='D':value=p['model']+' area='+value
    elif kind in {'Q','J'}:value=p['model']+' '+value
    elif kind=='M':value=p['model']+f' L=1u W={c["value"]:.12g}u'
    elif kind=='S':value=p['model']
    elif kind=='X':
        value=p['model']
        if p['id'] in {'opamp','comparator'}:value+=f' gain={c["value"]:.12g}'
        elif p['id']=='potentiometer':value+=f' resistance={c["value"]:.12g} ratio={c.get("ratio",.5):.12g}'
        elif p['id']!='bridge':value+=f' vdd={c["value"]:.12g}'
    return f'{c["id"]} {nodes} {value}'


def model_cards():
    cards=['.model MINA_SILICON D(Is=2.52n N=1.752 Rs=0.568 Cjo=4p Tt=20n)',
        '.model MINA_SCHOTTKY D(Is=1u N=1.05 Rs=0.1 Cjo=20p)',
        '.model MINA_NPN NPN(Is=1e-14 Bf=100 Vaf=100 Cje=10p Cjc=4p Tf=300p)',
        '.model MINA_PNP PNP(Is=1e-14 Bf=100 Vaf=100 Cje=10p Cjc=4p Tf=300p)',
        '.model MINA_NMOS NMOS(Level=1 Vto=2 Kp=0.05 Lambda=0.01)',
        '.model MINA_PMOS PMOS(Level=1 Vto=-2 Kp=0.05 Lambda=0.01)',
        '.model MINA_NJFET NJF(Vto=-2 Beta=0.001 Lambda=0.01)',
        '.model MINA_PJFET PJF(Vto=-2 Beta=0.001 Lambda=0.01)',
        '.model MINA_SWITCH SW(Ron=1 Roff=1e9 Vt=2.5 Vh=0)',
        '.model MINA_CLAMP D(Is=1e-9 N=0.0001 Rs=1u)',
        '.subckt MINA_OPAMP plus minus out vp vn params: gain=100000',
        'Gdiff vn internal plus minus {gain/1e6}',
        'Rgain internal vn 1e6','Dhi internal vp MINA_CLAMP','Dlo vn internal MINA_CLAMP',
        'Ebuffer out vn internal vn 1',
        'Rplus plus vn 1e12','Rminus minus vn 1e12','.ends MINA_OPAMP',
        '.subckt MINA_POT top wiper bottom params: resistance=10000 ratio=0.5',
        'Rtop top wiper {max(resistance*(1-ratio),1u)}',
        'Rbottom wiper bottom {max(resistance*ratio,1u)}','.ends MINA_POT',
        '.subckt MINA_BRIDGE ac1 ac2 plus minus',
        'D1 ac1 plus MINA_SILICON','D2 ac2 plus MINA_SILICON',
        'D3 minus ac1 MINA_SILICON','D4 minus ac2 MINA_SILICON','.ends MINA_BRIDGE']
    for model,bv in [('MINA_Z3V3',3.3),('MINA_Z5V1',5.1),('MINA_Z12',12)]:
        cards.append(f'.model {model} D(Is=1n N=1.5 Rs=2 Bv={bv} Ibv=1m)')
    for color,emission in [('RED',3),('GREEN',3.5),('BLUE',4.7),('WHITE',4.7)]:
        cards.append(f'.model MINA_LED_{color} D(Is=1e-12 N={emission} Rs=5)')
    a='(v(a,gnd)>vdd/2)';b='(v(b,gnd)>vdd/2)'
    gates=dict(AND=f'{a} && {b}',NAND=f'!({a} && {b})',OR=f'{a} || {b}',NOR=f'!({a} || {b})',XOR=f'{a} != {b}',XNOR=f'{a} == {b}')
    for name,expression in gates.items():
        cards.extend([f'.subckt MINA_{name} a b out gnd params: vdd=5',f'Bdrive out gnd V=({expression}) ? vdd : 0','Ra a gnd 1e12','Rb b gnd 1e12',f'.ends MINA_{name}'])
    for name,expression in [('BUFFER',a),('INVERTER',f'!{a}')]:
        cards.extend([f'.subckt MINA_{name} a out gnd params: vdd=5',f'Bdrive out gnd V=({expression}) ? vdd : 0','Ra a gnd 1e12',f'.ends MINA_{name}'])
    return '\n'.join(cards)+'\n'


def reference_project(part_id):
    """Small load/bias fixture for exercising a catalog preset, also downloadable."""
    p=BY_ID[part_id];kind=p['type']
    def c(t,i,v,**pins):return dict(type=t,id=i,value=v,x=300,y=200,rotation=0,**pins)
    def v(i,n,value):return c('V',i,value,a=n,b='0')
    def r(i,a,b,value=1000):return c('R',i,value,a=a,b=b)
    device=c(kind,kind+'dut',p['value'],part=p['id'])
    if 'wave' in p:device.update(wave=p['wave'],frequency=1000)
    if kind in {'R','C','L','D'}:
        device.update(a='out',b='0');items=[v('Vbias','supply',5),r('Rbias','supply','out'),device]
    elif kind in {'V','I'}:
        device.update(a='out' if kind=='V' else '0',b='0' if kind=='V' else 'out');items=[device,r('Rload','out','0')]
    elif kind in {'Q','M','J'}:
        negative=part_id in {'pnp','pmos','pjfet'};s=-1 if negative else 1
        device.update(a='out',b='control',c='0')
        if kind=='M':device['d']='0'
        items=[v('Vbias','supply',5*s),v('Vcontrol','control',(.7 if kind=='Q' else 3 if kind=='M' else 0)*s),r('Rload','supply','out'),device]
    elif kind in {'E','G','S'}:
        device.update(a='out',b='0',c='control',d='0');items=[v('Vcontrol','control',5),device,r('Rload','out','0')]
        if kind=='S':items=[v('Vbias','supply',5),v('Vcontrol','control',5),r('Rload','out','0'),device];device['a']='supply';device['b']='out'
    elif part_id in {'opamp','comparator'}:
        device.update(a='control',b='0' if part_id=='comparator' else 'out',c='out',d='supply',e='0');items=[v('Vbias','supply',5),v('Vcontrol','control',1),device,r('Rload','out','0',10000)]
    elif part_id=='potentiometer':
        device.update(a='supply',b='out',c='0',ratio=.5);items=[v('Vbias','supply',5),device]
    elif part_id=='bridge':
        device.update(a='supply',b='0',c='out',d='negative');items=[v('Vbias','supply',5),device,r('Rload','out','negative'),r('Rreference','negative','0',1e9)]
    elif part_id in {'buffer','inverter'}:
        device.update(a='control',b='out',c='0');items=[v('Vcontrol','control',5),device,r('Rload','out','0',10000)]
    else:
        device.update(a='ina',b='inb',c='out',d='0');items=[v('Va','ina',5),v('Vb','inb',0),device,r('Rload','out','0',10000)]
    for i,item in enumerate(items):item.update(x=180+(i%4)*200,y=220+(i//4)*200)
    for item in items:
        if item['type']=='V' or item['type']=='R' and item.get('b')=='0':item['rotation']=90
    if kind in {'Q','M','J'}:
        items[0].update(x=180,y=260);items[1].update(x=400,y=380)
        items[2].update(x=600,y=160,rotation=0);device.update(x=800,y=260)
    elif part_id in {'opamp','comparator'}:
        items[0].update(x=180,y=180);items[1].update(x=180,y=380)
        device.update(x=560,y=260);items[-1].update(x=800,y=260)
    nets={}
    for item in items:
        for pin in pins_for(item):nets.setdefault(item[pin],[]).append(item['id']+':'+pin)
    wires=[]
    for refs in nets.values():
        # Prefer an external endpoint so a feedback net routes through the load.
        anchor=next((r for r in refs if not r.startswith(device['id']+':')),refs[0])
        wires.extend(dict(a=anchor,b=r) for r in refs if r!=anchor)
    return dict(version=1,name=p['name']+' reference',components=items,wires=wires,analysis=dict(stop=.002,step=.00001))
