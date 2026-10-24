"""Real solver tests: these fail if a terminal/model is omitted or misrouted."""
import copy
import math
import unittest
from circuit import simulate, validate, netlist


def component(kind, ident, value, **pins):
    return dict(type=kind, id=ident, value=value, x=300, y=200, rotation=0, **pins)


def project(*items):
    return dict(version=1, name='Reference', components=list(items), wires=[], analysis=dict(stop=.001, step=.00001))


def voltage(ident, node, value):
    return component('V', ident, value, a=node, b='0')


class ExpandedAnalogTests(unittest.TestCase):
    def test_current_source_obeys_ohms_law(self):
        p=project(component('I','I1',.001,a='0',b='out'),component('R','R1',1000,a='out',b='0'))
        self.assertAlmostEqual(simulate(p)['dc']['out'],1,places=5)

    def test_transistor_control_terminal_changes_load_voltage(self):
        for kind,part in [('Q','npn'),('M','nmos')]:
            pins=dict(a='out',b='control',c='0')
            if kind=='M':pins['d']='0'
            device=component(kind,kind+'1',1,part=part,**pins)
            p=project(voltage('V1','supply',5),voltage('V2','control',0),component('R','R1',1000,a='supply',b='out'),device)
            self.assertGreater(simulate(p)['dc']['out'],4.9)
            p['components'][1]['value']=.8 if kind=='Q' else 5
            self.assertLess(simulate(p)['dc']['out'],.2)

    def test_opamp_closed_loop_gain_and_supply_clipping(self):
        p=project(voltage('V1','supply',5),voltage('V2','input',1),
            component('X','X1',100000,part='opamp',a='input',b='feedback',c='out',d='supply',e='0'),
            component('R','R1',10000,a='out',b='feedback'),component('R','R2',10000,a='feedback',b='0'))
        self.assertAlmostEqual(simulate(p)['dc']['out'],2,delta=.001)
        p['components'][1]['value']=4
        self.assertAlmostEqual(simulate(p)['dc']['out'],5,delta=.001)

    def test_logic_truth_tables_use_executed_solver(self):
        tables={'and':[0,0,0,5],'nand':[5,5,5,0],'or':[0,5,5,5],'nor':[5,0,0,0],'xor':[0,5,5,0],'xnor':[5,0,0,5]}
        for gate,want in tables.items():
            for i,(a,b) in enumerate([(0,0),(0,5),(5,0),(5,5)]):
                with self.subTest(gate=gate,a=a,b=b):
                    p=project(voltage('V1','ina',a),voltage('V2','inb',b),component('X','X1',5,part=gate,a='ina',b='inb',c='out',d='0'),component('R','R1',10000,a='out',b='0'))
                    self.assertAlmostEqual(simulate(p)['dc']['out'],want[i],places=4)

    def test_potentiometer_wiper_ratio(self):
        p=project(voltage('V1','supply',10),component('X','X1',10000,part='potentiometer',a='supply',b='out',c='0',ratio=.25))
        self.assertAlmostEqual(simulate(p)['dc']['out'],2.5,places=4)

    def test_zener_reverse_breakdown_and_led_forward_curves(self):
        p=project(voltage('V1','supply',10),component('R','R1',1000,a='supply',b='out'),component('D','D1',1,part='zener-5v1',a='0',b='out'))
        self.assertAlmostEqual(simulate(p)['dc']['out'],5.1,delta=.15)
        drops=[]
        for part in ['led-red','led-green','led-blue']:
            p=project(component('I','I1',.001,a='0',b='out'),component('D','D1',1,part=part,a='out',b='0'))
            drops.append(simulate(p)['dc']['out'])
        self.assertLess(drops[0],drops[1]);self.assertLess(drops[1],drops[2])

    def test_dependent_sources_and_switch_follow_control(self):
        for kind,part,value,want in [('E','vcvs',3,6),('G','vccs',.001,-2)]:
            p=project(voltage('V1','control',2),component(kind,kind+'1',value,part=part,a='out',b='0',c='control',d='0'),component('R','R1',1000,a='out',b='0'))
            self.assertAlmostEqual(simulate(p)['dc']['out'],want,places=4)
        p=project(voltage('V1','supply',5),voltage('V2','control',0),component('S','S1',1,part='voltage-switch',a='supply',b='out',c='control',d='0'),component('R','R1',1000,a='out',b='0'))
        self.assertLess(simulate(p)['dc']['out'],.001)
        p['components'][1]['value']=5;self.assertGreater(simulate(p)['dc']['out'],4.99)

    def test_missing_terminal_unknown_profile_and_mismatched_type_rejected(self):
        base=project(voltage('V1','supply',5),component('Q','Q1',1,part='npn',a='supply',b='0',c='0'))
        for mutate in [lambda c:c.pop('c'),lambda c:c.update(part='untrusted\n.control'),lambda c:c.update(part='nmos')]:
            p=copy.deepcopy(base);mutate(p['components'][1])
            with self.assertRaises(ValueError):validate(p)

    def test_every_registered_preset_solves_finite_reference_fixture(self):
        from analog_parts import PARTS, reference_project
        self.assertGreaterEqual(len(PARTS),35)
        for part in PARTS:
            with self.subTest(part=part['id']):
                p=reference_project(part['id']);r=simulate(p)
                self.assertGreater(r['samples'],10)
                self.assertTrue(all(math.isfinite(v) for v in r['dc'].values()))
                self.assertTrue(all(math.isfinite(v) for trace in r['traces'].values() for v in trace))

    def test_multiterminal_wire_validation_and_model_export(self):
        p=project(voltage('V1','control',5),component('Q','Q1',1,part='npn',a='out',b='control',c='0'),component('R','R1',1000,a='out',b='0'))
        p['wires']=[dict(a='Q1:c',b='V1:b')]
        self.assertIn('Q1 out control 0 MINA_NPN',netlist(p))
        p['wires'][0]['a']='Q1:d'
        with self.assertRaises(ValueError):validate(p)
