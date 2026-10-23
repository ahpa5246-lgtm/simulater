'use strict';
// Original bounded MPU-6050 I2C register model; not a motion physics engine.
// Source reference: TDK InvenSense RM-MPU-6000A-00 Rev 4.2.
function createMPU6050(config) {
  function vector(value, fallback, min, max, name) {
    const v = value === undefined ? fallback : value;
    if (!Array.isArray(v) || v.length !== 3 || v.some(n => typeof n !== 'number' || !Number.isFinite(n) || n < min || n > max))
      throw Error(`${name} must contain three finite values from ${min} to ${max}.`);
    return [...v];
  }
  const accelG = vector(config.accelG, [0, 0, 1], -16, 16, 'Acceleration (g)');
  const gyroDps = vector(config.gyroDps, [0, 0, 0], -2000, 2000, 'Angular velocity (deg/s)');
  const temperature = config.temperature === undefined ? 25 : config.temperature;
  if (typeof temperature !== 'number' || !Number.isFinite(temperature) || temperature < -40 || temperature > 85)
    throw Error('MPU-6050 temperature must be -40–85 °C.');
  const registers = new Uint8Array(128);
  let pointer = 0, expectPointer = false;
  function reset() { registers.fill(0); registers[0x6b] = 0x40; }
  reset();
  const encoded = (value, sensitivity) => Math.max(-32768, Math.min(32767, Math.round(value * sensitivity))) & 0xffff;
  function measurement(address) {
    if (registers[0x6b] & 0x40) return 0;
    const accelScale = [16384, 8192, 4096, 2048][(registers[0x1c] >> 3) & 3];
    const gyroScale = [131, 65.5, 32.8, 16.4][(registers[0x1b] >> 3) & 3];
    let value = 0;
    if (address >= 0x3b && address <= 0x40) {
      const axis = Math.floor((address - 0x3b) / 2);
      value = (registers[0x6c] & (0x20 >> axis)) ? 0 : encoded(accelG[axis], accelScale);
    } else if (address >= 0x41 && address <= 0x42) {
      value = registers[0x6b] & 0x08 ? 0 : encoded(temperature - 36.53, 340);
    } else if (address >= 0x43 && address <= 0x48) {
      const axis = Math.floor((address - 0x43) / 2);
      value = (registers[0x6c] & (4 >> axis)) ? 0 : encoded(gyroDps[axis], gyroScale);
    }
    return (address % 2 === 1) ? (value >> 8 & 255) : (value & 255);
  }
  return {
    begin(write) { expectPointer = !!write; },
    write(byte) {
      if (!Number.isInteger(byte) || byte < 0 || byte > 255) throw Error('I2C data must be a byte.');
      if (expectPointer) { pointer = byte & 127; expectPointer = false; return; }
      const address = pointer;
      pointer = (pointer + 1) & 127;
      if (address === 0x6b && (byte & 0x80)) { reset(); return; }
      // Implement power, scale and sampling config; identity and measurements are read-only.
      if ([0x19, 0x1a, 0x1b, 0x1c, 0x6b, 0x6c].includes(address)) registers[address] = byte;
    },
    read() {
      const address = pointer;
      pointer = (pointer + 1) & 127;
      if (address === 0x75) return 0x68; // WHO_AM_I excludes the AD0 bit.
      if (address >= 0x3b && address <= 0x48) return measurement(address);
      return registers[address];
    },
    snapshot() { return { model: 'mpu6050', address: config.address ?? 0x68, accelG, gyroDps, temperature,
      asleep: !!(registers[0x6b] & 0x40), accelFullScaleG: [2,4,8,16][(registers[0x1c] >> 3) & 3],
      gyroFullScaleDps: [250,500,1000,2000][(registers[0x1b] >> 3) & 3],
      pointer, limitations: 'Ideal registers only: no physics, DMP, FIFO, interrupts, noise, calibration or sample latency.' }; }
  };
}
module.exports = {createMPU6050};
