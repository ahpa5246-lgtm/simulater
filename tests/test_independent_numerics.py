"""Independent seeded numerical audit: no simulator-derived reference values."""
import json
import math
from pathlib import Path
import random
import unittest
import os
import tempfile
from unittest.mock import patch
from analyses import analyze

SEED = 20261024


def project(parts, analysis=None):
    return {'version': 1, 'name': 'Independent numerical audit', 'components': [
        dict(type=kind, id=cid, value=value, a=a, b=b, **extra)
        for kind, cid, value, a, b, extra in parts], 'wires': [],
        'analysis': analysis or {'stop': .005, 'step': .00001}}


def part(kind, cid, value, a, b, **extra):
    return kind, cid, value, a, b, extra


class IndependentNumericalTests(unittest.TestCase):
    def test_seeded_circuits_against_independent_equations(self):
        target=Path(__file__).resolve().parents[1]/'evidence/independent-numerical-audit.json'
        target.write_text(json.dumps(dict(seed=SEED,passed=False,status='running'))+'\n')
        rng = random.Random(SEED)
        evidence = []

        def compare(actual, expected, label, relative=2e-6, absolute=1e-9):
            tolerance = absolute + relative * abs(expected)
            error = abs(actual - expected)
            self.assertLessEqual(error, tolerance, f'{label}: {actual} != {expected}')
            return dict(label=label, actual=actual, expected=expected,
                        absoluteError=error, tolerance=tolerance, passed=True)

        # Unequal dividers with both polarities; Ohm, KCL and energy conservation.
        for index in range(30):
            voltage = rng.uniform(-24, 24)
            r1, r2 = (10 ** rng.uniform(1, 5) for _ in range(2))
            p = project([part('V','Vin',voltage,'in','0'),
                         part('R','R1',r1,'in','out'),part('R','R2',r2,'out','0')])
            result = analyze(p, {'type':'op'})
            current = voltage / (r1+r2)
            checks = [compare(result['traces']['out'][0], voltage*r2/(r1+r2), 'divider Vout'),
                      compare(result['currents']['R1'][0], current, 'resistor current'),
                      compare(result['currents']['Vin'][0], -current, 'source current'),
                      compare(sum(x[0] for x in result['power'].values()), 0, 'power balance', absolute=1e-6)]
            evidence.append(dict(family='DC divider', index=index, checks=checks))

        # Two unknown node voltages solved independently with a 2x2 determinant.
        for index in range(20):
            voltage = rng.uniform(1, 20)
            r1, r2, r3, r4, r5 = (10 ** rng.uniform(2, 4) for _ in range(5))
            g1,g2,g3,g4,g5 = (1/r for r in (r1,r2,r3,r4,r5))
            a,d,b = g1+g2+g5,g3+g4+g5,-g5
            det = a*d-b*b
            v1,v2 = (voltage*g1*d-b*voltage*g3)/det,(a*voltage*g3-b*voltage*g1)/det
            p = project([part('V','Vin',voltage,'in','0'),part('R','R1',r1,'in','n1'),
                         part('R','R2',r2,'n1','0'),part('R','R3',r3,'in','n2'),
                         part('R','R4',r4,'n2','0'),part('R','R5',r5,'n1','n2')])
            result = analyze(p, {'type':'op'})
            i = result['currents']
            checks = [compare(result['traces']['n1'][0],v1,'bridge node 1'),
                      compare(result['traces']['n2'][0],v2,'bridge node 2'),
                      compare(i['R1'][0]-i['R2'][0]-i['R5'][0],0,'KCL node 1',absolute=1e-9),
                      compare(i['R3'][0]+i['R5'][0]-i['R4'][0],0,'KCL node 2',absolute=1e-9)]
            evidence.append(dict(family='Resistive bridge', index=index, checks=checks))

        # Series RLC: compare complex phasors, not just plausible magnitudes.
        for index in range(40):
            resistance = 10 ** rng.uniform(1, 4)
            inductance = 10 ** rng.uniform(-4, -1)
            capacitance = 10 ** rng.uniform(-8, -4)
            frequency = 10 ** rng.uniform(1, 5)
            amplitude = rng.uniform(.1, 10)
            omega = 2*math.pi*frequency
            impedance = resistance + 1j*omega*inductance + 1/(1j*omega*capacitance)
            current = amplitude/impedance
            capacitor_voltage = current/(1j*omega*capacitance)
            p = project([part('V','Vin',0,'in','0'),part('R','R1',resistance,'in','mid'),
                         part('L','L1',inductance,'mid','out'),part('C','C1',capacitance,'out','0')])
            result = analyze(p,dict(type='ac',source='Vin',startHz=frequency,stopHz=frequency*10,
                                    pointsPerDecade=1,amplitude=amplitude))
            checks = [compare(result['voltageReal']['out'][0],capacitor_voltage.real,'RLC real Vc'),
                      compare(result['voltageImag']['out'][0],capacitor_voltage.imag,'RLC imaginary Vc'),
                      compare(result['currentReal']['R1'][0],current.real,'RLC real I'),
                      compare(result['currentImag']['R1'][0],current.imag,'RLC imaginary I'),
                      compare(result['power']['R1'][0],.5*abs(current)**2*resistance,'average R power'),
                      compare(sum(x[0] for x in result['power'].values()),0,'AC power balance',absolute=1e-7)]
            evidence.append(dict(family='Complex RLC', index=index, checks=checks))

        # RC charge: compare every useful time sample to the exponential law.
        for index in range(20):
            resistance=10**rng.uniform(2,4); capacitance=10**rng.uniform(-7,-5)
            voltage=rng.uniform(.5,12);tau=resistance*capacitance
            p=project([part('V','Vin',voltage,'in','0',wave='pulse',frequency=1),
                       part('R','R1',resistance,'in','out'),part('C','C1',capacitance,'out','0')],
                      dict(stop=4*tau,step=tau/500))
            result=analyze(p,{'type':'transient'})
            errors=[abs(v-voltage*(1-math.exp(-t/tau)))/voltage
                    for t,v in zip(result['axis'],result['traces']['out']) if t>tau/20]
            self.assertLess(max(errors),.003)
            evidence.append(dict(family='RC exponential',index=index,maxFullScaleError=max(errors),samplesChecked=len(errors),passed=True))

        report=dict(seed=SEED,circuitCases=len(evidence),pointComparisons=sum(len(c.get('checks',[])) for c in evidence),transientSamplesChecked=sum(c.get('samplesChecked',0) for c in evidence),passed=True,
                    scope='Independent equations for ideal resistor/RLC/RC cases; not physical hardware validation.',cases=evidence)
        target=Path(__file__).resolve().parents[1]/'evidence/independent-numerical-audit.json'
        target.write_text(json.dumps(report,indent=2)+'\n')
        self.assertEqual(len(evidence),110)

    def test_missing_native_engine_cannot_produce_a_successful_result(self):
        # Deliberately remove the engine for this call; no mocked numerical output.
        p=project([part('V','Vin',10,'in','0'),part('R','R1',1000,'in','0')])
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ,{'NGSPICE_BIN':str(Path(directory)/'absent-ngspice')}):
                with self.assertRaises(FileNotFoundError):analyze(p,{'type':'op'})
