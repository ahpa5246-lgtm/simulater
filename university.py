"""Wired undergraduate experiments and independent analytical reference checks."""
import copy
import math
from analog_parts import pins_for
from analyses import analyze


def _project(title,parts,stop=.01,step=.00001):
    components=[]
    for i,(kind,cid,value,a,b,*extra) in enumerate(parts):
        c=dict(type=kind,id=cid,value=value,a=a,b=b,x=140+(i%4)*180,y=160+(i//4)*180,rotation=90 if b=='0' else 0)
        if extra:c.update(extra[0])
        components.append(c)
    nets={}
    for c in components:
        for p in pins_for(c):nets.setdefault(c[p],[]).append(c['id']+':'+p)
    wires=[dict(a=refs[0],b=r) for refs in nets.values() for r in refs[1:]]
    return dict(version=1,name=title,components=components,wires=wires,analysis=dict(stop=stop,step=step))


def _catalog():
    entries=[]
    def add(cid,title,arabic,category,objective,equation,parts,analysis,checks,**timing):
        entries.append((dict(id=cid,title=title,titleAr=arabic,category=category,objective=objective,equation=equation,project=_project(title,parts,**timing),analysis=analysis),checks))
    v=('V','Vin',10,'in','0')
    add('ohms-law','Ohm’s law','قانون أوم','DC fundamentals','Measure resistance current and absorbed power.','I=V/R; P=V²/R',[v,('R','R1',1000,'in','0')],{'type':'op'},[('currents','R1',0,.01,1e-6),('power','R1',0,.1,1e-6)])
    divider=[v,('R','R1',1000,'in','out'),('R','R2',2000,'out','0')]
    add('voltage-divider','Voltage divider','مقسم الجهد','DC fundamentals','Verify the unloaded voltage divider.','Vout=Vin R2/(R1+R2)',divider,{'type':'op'},[('traces','out',0,20/3,1e-5)])
    add('series-resistors','Series resistors','المقاومات على التوالي','DC fundamentals','Verify equivalent resistance and common branch current.','I=V/(R1+R2)',divider,{'type':'op'},[('currents','R1',0,1/300,1e-7),('currents','R2',0,1/300,1e-7)])
    add('parallel-resistors','Parallel resistors','المقاومات على التوازي','DC fundamentals','Measure current splitting and source current.','Is=−V(1/R1+1/R2)',[v,('R','R1',1000,'in','0'),('R','R2',2000,'in','0')],{'type':'op'},[('currents','Vin',0,-.015,1e-7)])
    add('loaded-divider','Loaded voltage divider','مقسم الجهد المحمل','DC fundamentals','Observe loading by a finite output resistance.','Vout=Vin (R2∥RL)/(R1+R2∥RL)',divider+[('R','Rload',2000,'out','0')],{'type':'op'},[('traces','out',0,5,1e-5)])
    add('dc-divider-sweep','Divider DC sweep','مسح مقسم الجهد','DC sweeps','Measure linear transfer slope over a source sweep.','Vout=2 Vin/3',divider,{'type':'dc','source':'Vin','start':0,'stop':12,'step':1},[('traces','out',-1,8,1e-5),('traces','out',6,4,1e-5)])
    add('dc-current-sweep','Resistor current sweep','مسح تيار المقاومة','DC sweeps','Observe signed source current through negative and positive bias.','I(Vin)=−Vin/R',[v,('R','R1',1000,'in','0')],{'type':'dc','source':'Vin','start':-5,'stop':5,'step':1},[('currents','Vin',0,.005,1e-7),('currents','Vin',-1,-.005,1e-7)])
    fc=1/(2*math.pi*.001)
    ac=dict(type='ac',source='Vin',startHz=fc,stopHz=fc*100,pointsPerDecade=30,amplitude=1)
    rc=[v,('R','R1',1000,'in','out'),('C','C1',1e-6,'out','0')]
    add('rc-lowpass','RC low-pass cutoff','مرشح RC منخفض التمرير','AC filters','Verify the half-power cutoff and phase lag.','H=1/(1+jωRC); fc=1/(2πRC)',rc,ac,[('gainDb','out',0,-3.0102999566,.001),('phaseDeg','out',0,-45,.001)])
    add('rc-highpass','RC high-pass cutoff','مرشح RC عالي التمرير','AC filters','Verify the high-pass cutoff and phase lead.','H=jωRC/(1+jωRC)',[v,('C','C1',1e-6,'in','out'),('R','R1',1000,'out','0')],ac,[('gainDb','out',0,-3.0102999566,.001),('phaseDeg','out',0,45,.001)])
    rl_ac=dict(ac,startHz=1000/(2*math.pi*.1),stopHz=1000/(2*math.pi*.1)*100)
    add('rl-lowpass','RL low-pass cutoff','مرشح RL منخفض التمرير','AC filters','Compare the inductive low-pass response with RC.','H=R/(R+jωL)',[v,('L','L1',.1,'in','out'),('R','R1',1000,'out','0')],rl_ac,[('gainDb','out',0,-3.0102999566,.001),('phaseDeg','out',0,-45,.001)])
    add('rl-highpass','RL high-pass cutoff','مرشح RL عالي التمرير','AC filters','Measure voltage across an inductor at cutoff.','H=jωL/(R+jωL)',[v,('R','R1',1000,'in','out'),('L','L1',.1,'out','0')],rl_ac,[('gainDb','out',0,-3.0102999566,.001),('phaseDeg','out',0,45,.001)])
    # SIN starts at zero; ngspice solves the steady DC bias before transient.
    sine=('V','Vin',1,'in','0',dict(wave='sine',frequency=1000))
    add('ac-resistive-power','Sinusoidal resistor power','قدرة المقاومة المتناوبة','AC fundamentals','Relate peak phasors to average dissipated power.','Pavg=Vpeak²/(2R)',[sine,('R','R1',1000,'in','0')],dict(ac,startHz=1000,stopHz=10000,amplitude=2),[('power','R1',0,.002,1e-8)])
    add('transient-divider','Transient resistive transfer','الاستجابة الزمنية للمقسم','Transient','Verify a divider at every transient sample.','Vout(t)=Vin(t)/2',[sine,('R','R1',1000,'in','out'),('R','R2',1000,'out','0')],{'type':'transient'},[('ratio','out',0,.5,1e-6)],stop=.003)
    pulse=('V','Vin',5,'in','0',dict(wave='pulse',frequency=10))
    add('rc-step','RC charging step','شحن المكثف','Transient dynamics','Measure charging after one RC time constant.','Vc(τ)=Vs(1−exp(−1)); τ=RC',[pulse,('R','R1',1000,'in','out'),('C','C1',1e-6,'out','0')],{'type':'transient'},[('atTime','out',.001,5*(1-math.exp(-1)),.015)],stop=.005,step=.000002)
    add('rl-step','RL current step','الاستجابة الزمنية للملف','Transient dynamics','Measure inductor current after one L/R time constant.','IL(τ)=Vs/R (1−exp(−1)); τ=L/R',[pulse,('R','R1',100,'in','out'),('L','L1',.1,'out','0')],{'type':'transient'},[('currentAtTime','L1',.001,.05*(1-math.exp(-1)),.00015)],stop=.005,step=.000002)
    add('zener-regulator','Zener shunt regulator','منظم جهد زينر','Semiconductor circuits','Compare the reverse-biased shunt voltage to nominal breakdown.','Vout≈Vz; IR=(Vin−Vz)/R',[('V','Vin',12,'in','0'),('R','R1',1000,'in','out'),('D','D1',1,'0','out',dict(part='zener-5v1'))],{'type':'op'},[('traces','out',0,5.1,.3)])
    add('half-wave-rectifier','Half-wave rectifier','مقوم نصف الموجة','Semiconductor circuits','Measure the positive peak and rejection of the negative half-cycle.','Vout,peak≈Vpeak−Vf',[('V','Vin',5,'in','0',dict(wave='sine',frequency=1000)),('D','D1',1,'in','out'),('R','R1',1000,'out','0')],{'type':'transient'},[('maximum','out',0,5-.65,.15),('minimum','out',0,0,.001)],stop=.003,step=.000002)
    add('opamp-inverter','Inverting op-amp','المضخم العاكس','Active circuits','Verify negative closed-loop gain with finite open-loop gain.','Vout=−(Rf/Rin)Vin / (1+(1+Rf/Rin)/A)',[('V','Vin',1,'in','0'),('V','Vpositive',15,'vp','0'),('V','Vnegative',-15,'vn','0'),('R','Rin',10000,'in','sum'),('R','Rf',20000,'sum','out'),('X','Xamp',100000,'0','sum',dict(part='opamp',c='out',d='vp',e='vn')),('R','Rload',10000,'out','0')],{'type':'op'},[('traces','out',0,-2/(1+3/100000),.002)])
    add('transistor-switch','NPN saturated switch','الترانزستور كمفتاح','Active circuits','Observe a saturated collector with a driven base and resistive load.','VCE,sat≈0.1 V; IC≈(VCC−VCE,sat)/RC',[('V','Vin',5,'in','0'),('V','Vbase',.8,'base','0'),('R','R1',1000,'in','out'),('Q','Q1',1,'out','base',dict(part='npn',c='0'))],{'type':'op'},[('traces','out',0,.1,.1),('currents','R1',0,.0049,.0001)])
    return entries


def experiments():
    return copy.deepcopy([entry for entry,checks in _catalog()])


def run_experiment(request):
    if not isinstance(request,dict):raise ValueError('Invalid experiment request.')
    eid=request.get('experiment',request.get('id'))
    selected=next(((e,c) for e,c in _catalog() if e['id']==eid),None)
    if selected is None:raise ValueError('Unknown university experiment.')
    experiment,specs=selected
    project=request.get('project',experiment['project']);settings=request.get('analysis',experiment['analysis'])
    unchanged=project==experiment['project'] and settings==experiment['analysis']
    result=analyze(project,settings);checks=[]
    if unchanged:
        for field,node,index,expected,tolerance in specs:
            if field in ('atTime','currentAtTime'):
                values=result['traces' if field=='atTime' else 'currents'][node]
                axis=result['axis'];upper=next((i for i,t in enumerate(axis) if t>=index),len(axis)-1);lower=max(0,upper-1)
                fraction=(index-axis[lower])/(axis[upper]-axis[lower]) if upper!=lower else 0
                actual=values[lower]+fraction*(values[upper]-values[lower])
            elif field in ('maximum','minimum'):
                actual=(max if field=='maximum' else min)(result['traces'][node])
            elif field=='ratio':
                pairs=list(zip(result['traces']['in'],result['traces'][node]));a,b=max(pairs,key=lambda pair:abs(pair[0]));actual=b/a
            else:actual=result[field][node][index]
            checks.append(dict(label=f'{field}: {node}',actual=actual,expected=expected,tolerance=tolerance,passed=abs(actual-expected)<=tolerance))
    return dict(experiment=experiment,result=result,checks=checks,referenceUnmodified=unchanged,gradingNote='Analytical reference checks apply to the unmodified reference only.' if unchanged else 'Reference grading disabled: project or analysis settings were edited.')
