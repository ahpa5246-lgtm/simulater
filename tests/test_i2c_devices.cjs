const test=require('node:test'),assert=require('node:assert/strict');
let createI2CBus;try{({createI2CBus}=require('../boards/i2c-devices.cjs'));}catch{}
function clock(){return {cycles:0};}
function write(bus,address,bytes){assert.equal(bus.connect(address,true),true);for(const b of bytes)assert.equal(bus.write(b),true);bus.stop();}
function read(bus,address,n){assert.equal(bus.connect(address,false),true);const a=Array.from({length:n},()=>bus.read());bus.stop();return a;}
test('multiple independent devices, missing address and collisions',()=>{
 assert.equal(typeof createI2CBus,'function','multi-device bus missing');const cpu=clock();const bus=createI2CBus(cpu,[{model:'bh1750',lux:120,address:0x23},{model:'pcf8574',address:0x20,inputs:0xf0}]);
 assert.equal(bus.connect(0x77,true),false);assert.equal(bus.write(42),false);assert.equal(bus.read(),255);
 write(bus,0x20,[0xaa]);assert.deepEqual(read(bus,0x20,1),[0xa0]);
 assert.throws(()=>createI2CBus(cpu,[{model:'bh1750',address:0x23},{model:'bh1750',address:0x23}]),/address/i);
 assert.throws(()=>createI2CBus(cpu,[{model:'bh1750',lux:NaN}]),/lux/i);
});
test('BH1750 power and conversion timing affect bytes',()=>{
 assert.equal(typeof createI2CBus,'function');const cpu=clock(),bus=createI2CBus(cpu,[{model:'bh1750',lux:1000}]);
 assert.deepEqual(read(bus,0x23,2),[0,0]);write(bus,0x23,[1,0x10]);assert.deepEqual(read(bus,0x23,2),[0,0]);
 cpu.cycles=120*16000;assert.deepEqual(read(bus,0x23,2),[4,176]);
 write(bus,0x23,[0]);cpu.cycles+=120*16000;assert.deepEqual(read(bus,0x23,2),[4,176]);
});
test('ADS1115 reads zero before conversion, busy status, gain and signed differential input',()=>{
 assert.equal(typeof createI2CBus,'function');const cpu=clock(),bus=createI2CBus(cpu,[{model:'ads1115',voltages:[1,2,0,0]}]);
 assert.deepEqual(read(bus,0x48,2),[0,0]);
 write(bus,0x48,[1,0xc3,0x83]); // single AIN0, +/-4.096 V, 128 SPS
 assert.equal(read(bus,0x48,2)[0]&0x80,0);cpu.cycles=125000;
 write(bus,0x48,[0]);assert.deepEqual(read(bus,0x48,2),[0x1f,0x40]);
 write(bus,0x48,[1,0x83,0x83]);cpu.cycles+=125000;write(bus,0x48,[0]);assert.deepEqual(read(bus,0x48,2),[0xe0,0xc0]);
});
test('LM75 uses independent addresses, negative temperature and persistent pointer',()=>{
 assert.equal(typeof createI2CBus,'function');const bus=createI2CBus(clock(),[{model:'lm75',address:0x48,temperature:-10.5},{model:'lm75',address:0x49,temperature:25}]);
 write(bus,0x48,[0]);assert.deepEqual(read(bus,0x48,2),[0xf5,0x80]);assert.deepEqual(read(bus,0x49,2),[25,0]);
});
test('ADS1115 conversion in progress keeps its sampled configuration',()=>{
 const cpu=clock(),bus=createI2CBus(cpu,[{model:'ads1115',voltages:[1,2,0,0]}]);
 write(bus,0x48,[1,0xc3,0x83]);cpu.cycles=1000;write(bus,0x48,[1,0xd3,0x83]);cpu.cycles=125000;write(bus,0x48,[0]);assert.deepEqual(read(bus,0x48,2),[0x1f,0x40]);
});
