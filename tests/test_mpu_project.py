import unittest
from boards.projects import prepare_project
def project(c):return {'version':1,'board':'arduino-uno','durationMs':250,'components':[{'id':'imu',**c}]}
class MPUProject(unittest.TestCase):
 def test_catalogue_links_mpu_artwork_to_the_executable_model(self):
  from boards.project_service import capabilities
  row=next(r for r in capabilities()['records'] if r['id']=='wokwi-mpu6050')
  self.assertEqual(row['models'],['mpu6050'])
  self.assertEqual(row['status'],'behavioral-model-available')
 def test_addresses_and_defaults(self):
  for address in (104,105):
   d=prepare_project(project({'model':'mpu6050','address':address}))['i2cDevices'][0]
   self.assertEqual((d['address'],d['accelG'],d['gyroDps']),(address,[0,0,1],[0,0,0]))
 def test_rejects_bad_vectors_ranges_and_address(self):
  for c in ({'accelG':[1,2]},{'accelG':[0,0,17]},{'gyroDps':[0,2001,0]},{'accelG':[True,0,1]},{'address':106},{'temperature':100}):
   with self.subTest(c=c),self.assertRaises(ValueError):prepare_project(project({'model':'mpu6050',**c}))
 def test_conflicting_addresses_and_adc_pins(self):
  p=project({'model':'mpu6050'});p['components'].append({'id':'other','model':'mpu6050','address':104})
  with self.assertRaisesRegex(ValueError,'conflict'):prepare_project(p)
  p['components'][1]={'id':'analog','model':'lm35','pin':4,'value':25}
  with self.assertRaisesRegex(ValueError,'reserved'):prepare_project(p)
if __name__=='__main__':unittest.main()
