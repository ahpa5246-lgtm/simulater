# Firmware and instrument validation (v0.3)

The board runner executes ATmega328P instructions through AVR8js. Sensor models drive emulated pins or ADC voltages; firmware must read those pins. The logic analyser records actual PIN-register changes after instructions and clock events at a nominal 16 MHz. It does not draw illustrative waveforms. VCD (1 ns timestamps), CSV and execution JSON exports contain these recorded edges. Timing has instruction-boundary sampling error; nominal clock accuracy is assumed. Traces cap at 12,000 edges and explicitly report truncation. Truncated exports stop at the capture cutoff; they do not extend a fabricated flat signal to the execution end.

## Models and wiring

| Model | Connection | Implemented behavior |
| --- | --- | --- |
| LM35 / TMP36 | A0 | Ideal voltage/temperature transfer |
| Potentiometer / light divider | A0 | User-selected ideal 0–5 V input; no optical scene |
| NTC 10k | A0 | 10k pull-up, 10k at 25 °C, B3950 thermistor divider |
| Joystick axis | A0 | One normalized ideal analog axis |
| LM75 | SDA/SCL | Address 0x48 temperature-register subset; optional disconnected-address NACK |
| HC-SR04 | TRIG D3, ECHO D2 | At least 10 µs trigger; ideal 200 µs response delay; echo 58 µs/cm, 2–400 cm; optional no echo |
| Button / reed / IR obstacle | D2 | Ideal active-low digital signal |
| PIR | D2 | Ideal active-high digital signal |

Digital labels describe behavioral signal sources, not mechanical, magnetic, optical or motion physics. HC-SR04 has no acoustic scene, occlusion, noise or beam model. Reference: [HC-SR04 module datasheet](https://www.mouser.com/datasheet/2/813/HCSR04-1022824.pdf). Module variants differ. NTC parameters are generic, not a manufacturer-calibrated part.

## Reproducible checks

Click **Run verification suite** in Boards & sensors. It executes bundled HEX firmware afresh and compares observed results with explicit references. Downloaded reports include inputs, expected/measured values, error, tolerance, cycles, nominal clock, firmware SHA-256 and a trace preview. The committed `evidence/reference-verification.json` is one recorded run, not a substitute for running the suite.

Fourteen checks cover HC-SR04 at 20/100/200 cm (captured ECHO and firmware pulseIn independently), disconnected timeout, pressed/released button, NTC midpoint ADC, Timer1 pulse width/repetition, tone frequency and absent I²C address NACK. Formula checks establish internal consistency with documented ideal models. They are not comparison against physical boards, electrical conformance or proof of every sensor driver.

The ultrasonic reference disables interrupts during pulseIn to isolate timing; ordinary interrupt-enabled sketches can undercount because the polling routine cannot observe cycles spent in interrupts. The reference uses >60 ms between triggers. Timer1 produces a 1,500 µs / 20 ms servo-style signal: this tests PWM, not servo mechanics. Arduino AVR delayMicroseconds has limited argument range; a naive 18,500 µs call overflowed during development, correctly producing a wrong waveform. Hardware Timer1 replaced that erroneous reference sketch. Source and HEX are supplied together.

## Development checks

```
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_instruments.cjs tests/test_pico.cjs
node tests/browser.cjs
node tests/boards-browser.cjs
node tests/instruments-browser.cjs
```

Install Playwright Chromium first. Browser suites start their own loopback server; run them sequentially with port 8765 free. Python sensor tests compile real Arduino C++ fixtures and require the documented AVR toolchain. Browser examples and the reference suite can use bundled HEX without a compiler.

Missing capabilities include DHT/DS18B20 protocols, SPI sensor models, servo mechanics, arbitrary device models, hardware upload, full MCU debugging, oscilloscope triggering and analog/MCU co-simulation. Installing a driver library never supplies a missing device model.
