import copy
import unittest
from circuit import validate, netlist, simulate


def divider():
    return {'version':1,'name':'Divider','components':[
        {'id':'V1','type':'V','value':10,'a':'vin','b':'0','x':160,'y':200},
        {'id':'R1','type':'R','value':1000,'a':'vin','b':'out','x':320,'y':120},
        {'id':'R2','type':'R','value':1000,'a':'out','b':'0','x':480,'y':200}], 'wires':[]}


class CircuitTests(unittest.TestCase):
    def test_divider_measures_five_volts(self):
        result=simulate(divider())
        self.assertAlmostEqual(result['dc']['out'],5,places=5)
        self.assertIn('ngspice',result['engine'].lower())

    def test_rc_reaches_time_constant(self):
        p=divider(); p['components'][0]['wave']='pulse';p['components'][0]['value']=5;p['components'][0]['frequency']=10
        p['components'][2]={'id':'C1','type':'C','value':1e-6,'a':'out','b':'0','x':480,'y':200}
        p['analysis']={'stop':0.005,'step':0.00001}
        r=simulate(p);i=min(range(len(r['time'])),key=lambda i:abs(r['time'][i]-0.001))
        self.assertAlmostEqual(r['traces']['out'][i],5*(1-__import__('math').exp(-1)),delta=.03)

    def test_rejects_injected_node(self):
        p=divider();p['components'][0]['a']='v\n.control\nshell touch /tmp/evil'
        with self.assertRaises(ValueError):validate(p)

    def test_rejects_zero_resistance(self):
        p=divider();p['components'][1]['value']=0
        with self.assertRaises(ValueError):validate(p)

    def test_rejects_floating_network(self):
        p=divider()
        for c in p['components']:
            if c['b']=='0': c['b']='floating'
        with self.assertRaisesRegex(ValueError,'ground'):validate(p)

    def test_rejects_disconnected_island(self):
        p=divider();p['components'].append({'id':'R3','type':'R','value':100,'a':'a','b':'b','x':0,'y':0})
        with self.assertRaisesRegex(ValueError,'floating'):validate(p)

    def test_rejects_duplicate_ids(self):
        p=divider();p['components'][1]['id']='V1'
        with self.assertRaises(ValueError):validate(p)

    def test_netlist_contains_circuit(self):
        self.assertIn('R1 vin out 1000',netlist(divider()))

    def test_rejects_wire_that_disagrees_with_net(self):
        p=divider();p['wires']=[{'a':'V1:a','b':'R2:a'}]
        with self.assertRaisesRegex(ValueError,'wire'):validate(p)

    def test_input_is_not_mutated(self):
        p=divider();original=copy.deepcopy(p);netlist(p);self.assertEqual(p,original)

    def test_rejects_excessive_samples(self):
        p=divider();p['analysis']={'stop':1,'step':1e-12}
        with self.assertRaises(ValueError):validate(p)

if __name__=='__main__':unittest.main()
