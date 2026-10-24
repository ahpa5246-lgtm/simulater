"""Bounded native ngspice analyses; all solver expressions are generated here."""
import cmath
import math
import os
from pathlib import Path
import subprocess
import tempfile
from analog_parts import pins_for, spice_line, model_cards
from circuit import validate, engine_path


def _number(settings,key,default,lo,hi):
    v=settings.get(key,default)
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not lo<=v<=hi:
        raise ValueError(f'Invalid {key}: expected a finite number between {lo} and {hi}.')
    return v


def analyze(project,settings=None):
    try:validate(project)
    except (TypeError,KeyError,AttributeError,OverflowError) as exc:raise ValueError('Invalid circuit project fields.') from exc
    if settings is None:settings={'type':'transient'}
    if not isinstance(settings,dict):raise ValueError('Invalid analysis settings.')
    mode=settings.get('type','transient')
    if mode not in ('op','transient','ac','dc'):raise ValueError('Unsupported analysis mode.')
    components=project['components']; sources={c['id'].lower():c for c in components if c['type']=='V'}
    source=None; amplitude=1; sampling=None
    if mode in ('ac','dc'):
        sid=settings.get('source','')
        if not isinstance(sid,str) or sid.lower() not in sources:raise ValueError('Choose an existing voltage source.')
        source=sources[sid.lower()]['id']
    if mode=='ac':
        start=_number(settings,'startHz',10,1e-6,1e12);stop=_number(settings,'stopHz',1e6,1e-6,1e12)
        points=_number(settings,'pointsPerDecade',40,1,1000);amplitude=_number(settings,'amplitude',1,1e-12,1e6)
        if stop<=start or points!=int(points) or math.log10(stop/start)*points>20000:raise ValueError('AC requires an increasing range and at most 20,000 samples.')
        # ngspice 42 can divide by zero while building a logarithmic grid
        # with fewer than two intervals (including one-decade rounding).
        # A three-point linear sweep preserves both requested endpoints.
        if float(f'{stop:.12g}')<=float(f'{start:.12g}'):
            raise ValueError('AC frequency range is too narrow for solver precision.')
        sparse=math.log10(stop/start)*points<2
        sampling='linear-minimum-three' if sparse else 'logarithmic'
        command=(f'ac lin 3 {start:.12g} {stop:.12g}' if sparse else f'ac dec {int(points)} {start:.12g} {stop:.12g}');label='Frequency (Hz)'
    elif mode=='dc':
        start=_number(settings,'start',0,-1e6,1e6);stop=_number(settings,'stop',10,-1e6,1e6);step=_number(settings,'step',.1,-1e6,1e6)
        if step==0 or (stop-start)*step<=0 or abs((stop-start)/step)>20000:raise ValueError('DC step must follow the sweep direction; maximum 20,000 steps.')
        command=f'dc {source} {start:.12g} {stop:.12g} {step:.12g}';label='Source voltage (V)'
    elif mode=='transient':
        a=project.get('analysis',{});command=f'tran {a.get("step",.00001):.12g} {a.get("stop",.005):.12g}';label='Time (s)'
    else:command='op';label='Operating point'
    nodes=sorted({c[p].lower() for c in components for p in pins_for(c)}-{'0'})
    used={c['id'].lower() for c in components}|{c[p].lower() for c in components for p in pins_for(c)}
    lines=['University workbench generated trusted circuit']; measured=[]
    for index,c in enumerate(components):
        device=dict(c)
        if len(pins_for(c))==2:
            if c['type']=='V':branch=c['id'].lower()
            else:
                suffix=index
                while f'vmeasure{suffix}' in used or f'measure{suffix}' in used:suffix+=len(components)+1
                branch=f'vmeasure{suffix}';node=f'measure{suffix}';used.update((branch,node))
                lines.append(f'{branch} {c["a"].lower()} {node} 0');device['a']=node
            measured.append((c,branch))
        line=spice_line(device)
        if mode=='ac' and c['id']==source:line+=f' AC {amplitude:.12g}'
        lines.append(line)
    expressions=[f'v({n})' for n in nodes]+[f'i({b})' for c,b in measured]
    if not expressions:raise ValueError('No measurable circuit nodes.')
    if mode=='ac':expressions=[f'{func}({e})' for e in expressions for func in ('real','imag')]
    deck='\n'.join(lines)+'\n'+model_cards()+f'\n.control\nset noaskquit\nset wr_singlescale\nset numdgt=15\n{command}\nwrdata result.txt '+ ' '.join(expressions)+'\nquit\n.endc\n.end\n'
    with tempfile.TemporaryDirectory(prefix='mina-analysis-') as directory:
        path=Path(directory);(path/'circuit.cir').write_text(deck)
        env=dict(os.environ);lib=Path(__file__).parent/'.tools/usr/lib/x86_64-linux-gnu'
        if lib.is_dir():env['LD_LIBRARY_PATH']=str(lib.resolve())+':'+env.get('LD_LIBRARY_PATH','')
        try:r=subprocess.run([engine_path(),'-b','circuit.cir'],cwd=path,env=env,capture_output=True,text=True,timeout=15)
        except subprocess.TimeoutExpired as exc:raise ValueError('Solver exceeded the 15 second time limit.') from exc
        output=path/'result.txt'
        if r.returncode or not output.exists():raise ValueError('Simulation failed: '+(r.stderr or r.stdout)[-1500:])
        if output.stat().st_size>40_000_000:raise ValueError('Solver output exceeded the size limit.')
        rows=[]
        for line in output.read_text().splitlines():
            try:row=[float(v) for v in line.split()]
            except ValueError:raise ValueError('Solver returned invalid numeric results.')
            if len(row)!=len(expressions)+1 or not all(math.isfinite(v) for v in row):raise ValueError('Solver returned invalid numeric results.')
            rows.append(row)
        if not rows or len(rows)>50000:raise ValueError('Invalid solver sample count.')
        if mode=='ac' and (len(rows)<2 or any(a[0]>=b[0] for a,b in zip(rows,rows[1:]))):
            raise ValueError('Solver could not resolve distinct AC frequencies. Widen the frequency range.')
    count=len(nodes)+len(measured)
    vectors=[[complex(row[1+2*i],row[2+2*i]) if mode=='ac' else row[1+i] for row in rows] for i in range(count)]
    voltages=dict(zip(nodes,vectors));currents={c['id']:vectors[len(nodes)+i] for i,(c,b) in enumerate(measured)}
    power={}
    for c,b in measured:
        va=voltages.get(c['a'].lower(),[0]*len(rows));vb=voltages.get(c['b'].lower(),[0]*len(rows));current=currents[c['id']]
        power[c['id']]=[.5*((a-z)*i.conjugate()).real if mode=='ac' else (a-z)*i for a,z,i in zip(va,vb,current)]
    result=dict(engine='ngspice · native SPICE engine',mode=mode,axis=[r[0] for r in rows],axisLabel=label,traces=voltages,currents=currents,power=power,samples=len(rows),measurementNote='Two-terminal branch currents flow from pin a to b; voltage-source current retains ngspice sign. AC traces/currents are peak magnitudes; power is average real power.')
    if mode=='ac':
        result['sampling']=sampling
        if sampling=='linear-minimum-three':result['measurementNote']+=' Sparse AC range: three linearly spaced samples preserve both endpoints and avoid a degenerate native logarithmic grid.'
        result['voltageReal']={n:[v.real for v in vs] for n,vs in voltages.items()}
        result['voltageImag']={n:[v.imag for v in vs] for n,vs in voltages.items()}
        result['currentReal']={n:[v.real for v in vs] for n,vs in currents.items()}
        result['currentImag']={n:[v.imag for v in vs] for n,vs in currents.items()}
        result['currentPhaseDeg']={n:[math.degrees(cmath.phase(v)) for v in vs] for n,vs in currents.items()}
        result['gainDb']={n:[20*math.log10(max(abs(v)/amplitude,1e-300)) for v in vs] for n,vs in voltages.items()}
        result['phaseDeg']={n:[math.degrees(cmath.phase(v)) for v in vs] for n,vs in voltages.items()}
        result['traces']={n:[abs(v) for v in vs] for n,vs in voltages.items()};result['currents']={n:[abs(v) for v in vs] for n,vs in currents.items()}
    return result
