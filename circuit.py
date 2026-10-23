"""Validated circuit graph to bounded local ngspice batch simulation."""
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from analog_parts import KINDS, part_for, pins_for, spice_line, model_cards

NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,31}$|^0$')


def validate(project):
    if not isinstance(project, dict) or project.get('version') != 1:
        raise ValueError('Unsupported project format. Expected version 1.')
    components = project.get('components')
    if not isinstance(components, list) or not 1 <= len(components) <= 150:
        raise ValueError('A project needs 1–150 components.')
    seen, adjacency = set(), {}
    for c in components:
        if not isinstance(c, dict):
            raise ValueError('Invalid component.')
        kind, cid = c.get('type'), c.get('id', '')
        if kind not in KINDS or not isinstance(cid,str) or not NAME.fullmatch(cid) or not cid.startswith(kind):
            raise ValueError('Invalid component identifier or unsupported component type.')
        if cid.lower() in seen:
            raise ValueError('Duplicate component identifier.')
        seen.add(cid.lower())
        profile=part_for(c)
        for pin in pins_for(c):
            if not isinstance(c.get(pin),str) or not NAME.fullmatch(c[pin]):
                raise ValueError('Invalid node name. Use letters, numbers and underscores.')
        if len(pins_for(c))==2 and c['a'].lower() == c['b'].lower():
            raise ValueError(f'{cid}: both pins connect to the same node.')
        v = c.get('value')
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e9:
            raise ValueError(f'{cid}: enter a finite numeric value.')
        if kind in {'R','C','L','D','Q','M','J','X','S'} and v<=0:
            raise ValueError(f'{cid}: value must be greater than zero.')
        ratio=c.get('ratio',.5)
        if isinstance(ratio,bool) or not isinstance(ratio,(int,float)) or not math.isfinite(ratio) or not 0<=ratio<=1:
            raise ValueError('Potentiometer ratio must be between 0 and 1.')
        if c.get('wave','dc') not in {'dc','sine','pulse'}:
            raise ValueError('Unsupported source waveform.')
        frequency=c.get('frequency',1000)
        if not isinstance(frequency,(int,float)) or isinstance(frequency,bool) or not math.isfinite(frequency) or not 1<=frequency<=1e7:
            raise ValueError('Frequency must be between 1 Hz and 10 MHz.')
        for key in ('x','y','rotation'):
            position=c.get(key,0)
            if not isinstance(position,(int,float)) or isinstance(position,bool) or not math.isfinite(position) or abs(position)>100000:
                raise ValueError('Invalid component position.')
        nodes={c[k].lower() for k in pins_for(c)}
        for node in nodes:adjacency.setdefault(node,set()).update(nodes-{node})
    wires=project.get('wires',[])
    if not isinstance(wires,list) or len(wires)>500:raise ValueError('Invalid wire list.')
    by_id={c['id']:c for c in components}
    for wire in wires:
        try:
            if not isinstance(wire,dict):raise ValueError('Invalid wire.')
            first,second=(wire[k].split(':') for k in ('a','b'))
            if len(first)!=2 or len(second)!=2 or first[1] not in pins_for(by_id[first[0]]) or second[1] not in pins_for(by_id[second[0]]) or by_id[first[0]][first[1]].lower()!=by_id[second[0]][second[1]].lower():
                raise ValueError('A wire disagrees with its electrical node connections.')
        except (KeyError,TypeError,AttributeError):raise ValueError('Invalid wire endpoint.')
    if '0' not in adjacency:
        raise ValueError('Connect the circuit to ground (node 0).')
    reached={'0'};pending=['0']
    while pending:
        for node in adjacency[pending.pop()]-reached:
            reached.add(node);pending.append(node)
    if reached != set(adjacency):
        raise ValueError('The circuit contains floating nodes. Connect every network to ground.')
    analysis=project.get('analysis',{})
    if not isinstance(analysis,dict):raise ValueError('Invalid analysis settings.')
    stop,step=analysis.get('stop',.005),analysis.get('step',.00001)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (stop,step)) or stop>10 or step>stop or stop/step>20000:
        raise ValueError('Choose a positive duration ≤10 s and at most 20,000 time steps.')
    return project


def netlist(project):
    validate(project)
    lines=['Mina circuit workbench — generated netlist']
    for c in project['components']:
        lines.append(spice_line(c))
    return '\n'.join(lines)+'\n'+model_cards()


def engine_path():
    path=os.environ.get('NGSPICE_BIN') or shutil.which('ngspice')
    if not path:
        local=Path(__file__).parent/'.tools/usr/bin/ngspice'
        if local.exists():path=str(local.resolve())
    if not path:raise RuntimeError('ngspice is not installed. Install ngspice or set NGSPICE_BIN, then run again.')
    return path


def simulate(project):
    deck=netlist(project)
    nodes=sorted({c[p].lower() for c in project['components'] for p in pins_for(c)}-{'0'})
    analysis=project.get('analysis',{}); stop=analysis.get('stop',.005);step=analysis.get('step',.00001)
    expressions=' '.join(f'v({n})' for n in nodes)
    deck+=f'.control\nset noaskquit\nset wr_singlescale\nop\nwrdata dc.txt {expressions}\ntran {step:.12g} {stop:.12g}\nwrdata transient.txt {expressions}\nquit\n.endc\n.end\n'
    with tempfile.TemporaryDirectory(prefix='mina-circuit-') as directory:
        path=Path(directory);(path/'circuit.cir').write_text(deck)
        env={**os.environ,'SPICE_ASCIIRAWFILE':'1'}
        local_lib=Path(__file__).parent/'.tools/usr/lib/x86_64-linux-gnu'
        if local_lib.is_dir():env['LD_LIBRARY_PATH']=str(local_lib.resolve())+':'+env.get('LD_LIBRARY_PATH','')
        result=subprocess.run([engine_path(),'-b','circuit.cir'],cwd=path,capture_output=True,text=True,timeout=15,env=env)
        if result.returncode or not (path/'transient.txt').exists():
            raise ValueError('Simulation failed: '+(result.stderr or result.stdout)[-1500:])
        def read(filename):
            rows=[]
            for line in (path/filename).read_text().splitlines():
                try:row=[float(v) for v in line.split()]
                except ValueError:continue
                if len(row)!=len(nodes)+1 or not all(math.isfinite(v) for v in row):
                    raise ValueError('Solver returned invalid numeric results.')
                rows.append(row)
            if not rows:raise ValueError('Solver returned no measurements.')
            return rows
        dc,rows=read('dc.txt'),read('transient.txt')
        if len(rows)>50000:raise ValueError('Too many solver samples. Increase the time step.')
        return {'engine':'ngspice · native SPICE engine','time':[r[0] for r in rows], 'traces':{n:[r[i+1] for r in rows] for i,n in enumerate(nodes)},'dc':{n:dc[0][i+1] for i,n in enumerate(nodes)},'samples':len(rows)}
