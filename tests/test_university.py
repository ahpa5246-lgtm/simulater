import copy
import math
import unittest

class UniversityTests(unittest.TestCase):
    def test_native_modes_and_measurements(self):
        import analyses
        p={'version':1,'components':[dict(id='Vin',type='V',value=10,a='in',b='0'),dict(id='R1',type='R',value=1000,a='in',b='out'),dict(id='R2',type='R',value=1000,a='out',b='0')]}
        r=analyses.analyze(p,{'type':'op'})
        self.assertAlmostEqual(r['traces']['out'][0],5,places=5)
        self.assertAlmostEqual(r['currents']['Vin'][0],-.005,places=7)
        self.assertAlmostEqual(r['power']['R2'][0],.025,places=7)
        r=analyses.analyze(p,{'type':'dc','source':'Vin','start':0,'stop':10,'step':1})
        self.assertAlmostEqual(r['traces']['out'][-1],5,places=5)
        p['components'][-1]=dict(id='C1',type='C',value=1e-6,a='out',b='0')
        fc=1/(2*math.pi*.001)
        r=analyses.analyze(p,{'type':'ac','source':'Vin','startHz':fc,'stopHz':fc*10,'pointsPerDecade':10,'amplitude':2})
        self.assertAlmostEqual(r['gainDb']['out'][0],-3.0103,places=3)
        self.assertAlmostEqual(r['phaseDeg']['out'][0],-45,places=3)
        self.assertEqual(analyses.analyze(p,{'type':'transient'})['mode'],'transient')

    def test_invalid_settings(self):
        import analyses, university
        p=university.experiments()[0]['project']
        for s in [{'type':'ac','source':'Vin\nquit'},{'type':'dc','source':'Vin','start':0,'stop':10,'step':-1},{'type':'ac','source':'Vin','pointsPerDecade':True},{'type':'bogus'},{'type':'dc','source':[]}]:
            with self.subTest(s=s), self.assertRaises(ValueError): analyses.analyze(p,s)

    def test_all_experiments_and_modified_grading(self):
        import university
        records=university.experiments()
        self.assertGreaterEqual(len(records),19)
        for e in records:
            with self.subTest(experiment=e['id']):
                self.assertTrue(e['project']['wires'])
                r=university.run_experiment({'experiment':e['id']})
                self.assertTrue(r['referenceUnmodified'])
                self.assertTrue(r['checks'])
                self.assertTrue(all(c['passed'] for c in r['checks']),r['checks'])
        e=records[0]; p=copy.deepcopy(e['project']);p['components'][0]['value']+=1
        r=university.run_experiment({'id':e['id'],'project':p})
        self.assertFalse(r['referenceUnmodified']); self.assertEqual(r['checks'],[])

    def test_rejects_untrusted_shapes_and_bounds(self):
        import analyses, university
        p=university.experiments()[0]['project']
        for field,value in [('type',[]),('part',[]),('id',[]),('a',[]),('value',float('nan'))]:
            bad=copy.deepcopy(p);bad['components'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):analyses.analyze(bad,{'type':'op'})
        for settings in [[],{'type':'ac','source':'Vin','amplitude':0},{'type':'ac','source':'Vin','startHz':float('inf')},{'type':'ac','source':'Vin','stopHz':1},{'type':'dc','source':'Vin','step':1e-9},{'type':'ac','source':'Vin','pointsPerDecade':1.5}]:
            with self.subTest(settings=settings),self.assertRaises(ValueError):analyses.analyze(p,settings)

    def test_descending_sweep_and_ac_power(self):
        import analyses, university
        p=university.experiments()[0]['project']
        r=analyses.analyze(p,{'type':'dc','source':'Vin','start':5,'stop':-5,'step':-1})
        self.assertEqual(len(r['axis']),11)
        self.assertAlmostEqual(r['currents']['Vin'][-1],.005,places=7)
        r=analyses.analyze(p,{'type':'ac','source':'Vin','startHz':100,'stopHz':1000,'amplitude':2})
        self.assertAlmostEqual(r['power']['R1'][0],.002,places=8)
        self.assertAlmostEqual(r['power']['Vin'][0],-.002,places=8)
        self.assertAlmostEqual(r['currentReal']['Vin'][0],-.002,places=8)
        self.assertAlmostEqual(r['currentImag']['Vin'][0],0,places=8)

    def test_giant_json_integers_are_rejected(self):
        import analyses, university
        p=university.experiments()[0]['project']
        for mode,keys in [('ac',['amplitude','startHz','stopHz','pointsPerDecade']),('dc',['start','stop','step'])]:
            for key in keys:
                with self.subTest(mode=mode,key=key),self.assertRaises(ValueError):
                    analyses.analyze(p,dict(type=mode,source='Vin',**{key:10**400}))
        for key in ['value','frequency','ratio','x']:
            bad=copy.deepcopy(p);bad['components'][0][key]=10**400
            with self.subTest(key=key),self.assertRaises(ValueError):analyses.analyze(bad,{'type':'op'})
