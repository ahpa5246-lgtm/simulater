'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createMPU6050} = require('../boards/mpu6050.cjs');
const {createI2CBus} = require('../boards/i2c-devices.cjs');
function write(d, ptr, ...bytes) { d.begin(true);d.write(ptr);bytes.forEach(x=>d.write(x)); }
function read(d, ptr, size) {d.begin(true);d.write(ptr);d.begin(false);return Array.from({length:size},()=>d.read());}
function word(b,n) {return ((b[n]<<8)|b[n+1])<<16>>16;}
test('WHO_AM_I, sleep/wake and 14-byte motion data',()=>{
 const d=createMPU6050({accelG:[.5,0,1],gyroDps:[0,90,0],temperature:36.53});
 assert.deepEqual(read(d,0x75,1),[0x68]);
 assert.deepEqual(read(d,0x3b,14),Array(14).fill(0));
 write(d,0x6b,0);const b=read(d,0x3b,14);
 assert.equal(word(b,0),8192);assert.equal(word(b,4),16384);assert.equal(word(b,6),0);assert.equal(word(b,10),11790);
});
test('sensor full scales, axis standby, read-only identity, soft reset',()=>{
 const d=createMPU6050({accelG:[-4,0,1],gyroDps:[0,500,0]});
 write(d,0x6b,0);let b=read(d,0x3b,14);
 assert.equal(word(b,0),-32768);assert.equal(word(b,10),32767);
 write(d,0x1c,0x10);write(d,0x1b,0x10);b=read(d,0x3b,14);
 assert.equal(word(b,0),-16384);assert.equal(word(b,10),16400);
 write(d,0x6c,0x24);b=read(d,0x3b,14);assert.equal(word(b,0),0);assert.equal(word(b,8),0);
 write(d,0x75,0);assert.equal(read(d,0x75,1)[0],0x68);
 write(d,0x6b,0x80);assert.equal(d.snapshot().asleep,true);assert.equal(d.snapshot().accelFullScaleG,2);
});
test('invalid vectors and temperatures fail',()=>{
 for(const c of [{accelG:[0,0]},{gyroDps:[NaN,0,0]},{accelG:[0,0,17]},{temperature:-41}])assert.throws(()=>createMPU6050(c));
});
test('shared I2C bus routes, NACKs and rejects collisions',()=>{
 const bus=createI2CBus({cycles:0},[{model:'mpu6050',address:0x68,accelG:[1,0,0]},{model:'mpu6050',address:0x69,connected:false}]);
 assert.equal(bus.connect(0x68,true),true);bus.write(0x75);bus.stop();
 assert.equal(bus.connect(0x68,false),true);assert.equal(bus.read(),0x68);bus.stop();
 assert.equal(bus.connect(0x69,true),false);assert.equal(bus.snapshots().length,2);
 assert.throws(()=>createI2CBus({cycles:0},[{model:'mpu6050',address:0x68},{model:'mpu6050',address:0x68}]),/conflict/i);
});
