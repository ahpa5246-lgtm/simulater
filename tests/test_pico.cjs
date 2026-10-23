const test=require('node:test'),assert=require('node:assert/strict');
const {runPico,demoUF2}=require('../boards/pico.cjs');
test('Pico executes ARM firmware that toggles GPIO25',()=>{const r=runPico({uf2:demoUF2().toString('base64'),durationMs:1});assert.ok(r.transitions.length>5);assert.ok(r.cycles>100000);assert.equal(r.engine,'RP2040js 1.3.3');});
test('Pico rejects invalid UF2',()=>{assert.throws(()=>runPico({uf2:Buffer.alloc(512).toString('base64')}),/UF2/);});

test('Pico rejects unsupported CPU sleep instead of running through WFI',()=>{const b=demoUF2();b.writeUInt16LE(0xbf30,40);b.writeUInt16LE(0x2001,42);b.writeUInt16LE(0xbe00,44);assert.throws(()=>runPico({uf2:b.toString('base64'),durationMs:1}),/sleep/);});
