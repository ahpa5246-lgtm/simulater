import unittest
from pathlib import Path
from boards.protocols import decode_capture
from boards.service import run_board
class ProtocolDecoders(unittest.TestCase):
 def test_spi_from_executed_firmware(self):
  r=run_board({'board':'arduino-uno','hex':Path('examples/firmware/spi-trace.hex').read_text(),'durationMs':10})
  d=decode_capture({'protocol':'spi','pins':{'clk':'D13','mosi':'D11','cs':'D10'},'logic':r['logic'],'capturedCycles':r['evidence']['capturedCycles']})
  values=[p['data'][1] for p in d['packets'] if p['data'][0]=='DATA'];self.assertEqual(values[:2],[0xa5,0x3c])
 def test_uart_independent_known_frame(self):
  edges=[{'cycle':0,'pin':'D4','value':True}];cycle=1600;old=True
  for bit in [0]+[(0x55>>n)&1 for n in range(8)]+[1]:
   if bool(bit)!=old:edges.append({'cycle':cycle,'pin':'D4','value':bool(bit)});old=bool(bit)
   cycle+=1667
  d=decode_capture({'protocol':'uart','pins':{'rx':'D4'},'logic':edges,'capturedCycles':cycle+4000,'baud':9600})
  values=[p['data'][2][0] for p in d['packets'] if p['data'][0]=='DATA'];self.assertEqual(values,[0x55])
 def test_i2c_independent_address_and_nack(self):
  edges=[];cycle=0;state={'D4':False,'D5':False}
  def setpin(p,v):
   nonlocal cycle
   cycle+=100
   if state[p]!=v:edges.append({'cycle':cycle,'pin':p,'value':v});state[p]=v
  setpin('D4',True);setpin('D5',True);setpin('D4',False)
  for bit in [(0x90>>n)&1 for n in range(7,-1,-1)]+[1]:
   setpin('D5',False);setpin('D4',bool(bit));setpin('D5',True)
  setpin('D5',False);setpin('D4',False);setpin('D5',True);setpin('D4',True)
  d=decode_capture({'protocol':'i2c','pins':{'scl':'D5','sda':'D4'},'logic':edges,'capturedCycles':cycle+100})
  packets=[p['data'] for p in d['packets']];self.assertIn(['ADDRESS WRITE',0x48],packets);self.assertIn(['NACK',None],packets)
 def test_rejects_unsafe_options_and_reversed_edges(self):
  for config in [{'protocol':'../../x','pins':{}},{'protocol':'spi','pins':{'clk':'D1','mosi':'D1'}}]:
   with self.assertRaises(ValueError):decode_capture({**config,'logic':[],'capturedCycles':100})
