# Practical firmware simulation workspace

Open **Practical simulation** from the circuit or boards page (`/lab.html`).
This workspace compiles Arduino C++ against the existing AVR core/source
libraries and executes the resulting HEX instructions in AVR8js. Inputs enter
ADC/GPIO or device registers. Outputs and measurements come from executed CPU
instructions and scheduled device events; the UI never synthesizes serial results.

## Editable projects

A version-1 project contains a board (`arduino-uno` or classic `arduino-nano`),
an execution window of 1–1000 ms, and at most 32 components. Each component has
a unique ID, an explicit executable model, and pin or I2C address configuration.
The backend rejects unknown models, duplicate addresses, conflicting external
drivers, invalid ranges and attempts to use A4/A5 analog sources while I2C is
connected. The project supports up to six analog sources, eight digital devices
and sixteen I2C devices, within the overall limit. Multiple indicators may
observe one output pin. Nominal power and common ground are implicit.

Analog/digital inputs can include up to 64 strictly increasing scheduled changes:
`"changes": [{"atMs":100,"value":80}]`. Digital values must be booleans.
These changes are scheduled on the CPU clock and affect subsequent firmware reads.
I2C environment parameters are constant per run. Disconnecting a device removes
its input or causes an address NACK. Imported source libraries remain managed on
the existing board page and are used by project compilation as well.

Four executable experiments are shipped: a shared I2C bus with scheduled ADC and
button inputs; ADS1115 conversion; HC-SR04 pulseIn; and Timer1 servo command PWM.
Projects persist locally and can be exported/imported as JSON with source code.
Editing a project clears stale measurements. Exported results include serial,
GPIO edges/VCD, protocol transactions, model snapshots, stimulus events, firmware
SHA-256 and project configuration SHA-256.

## Models

The picker contains 20 behavioral/output model types: six existing analog sources,
four digital input types, HC-SR04, six I2C types, and LED/servo/buzzer indicators.
This is not a count of physically validated components.

The new byte-level bus supports independent addresses and persistent per-device
state. Existing LM75, PICSimLab DS1621 and BMP180 support remains available;
DS1621/BMP180 require the existing native adapter build. New models:

| Device | Implemented behavior | Important omissions |
| --- | --- | --- |
| ADS1115 | Pointer/config/conversion/threshold registers, MUX, PGA, signed conversion, nominal 8–860 SPS completion, busy status, single/continuous conversion | ALERT/comparator output, noise, source impedance, electrical overvoltage behavior |
| BH1750 | Power/reset and continuous/one-shot measurement commands, nominal completion time, MTreg adjustment and raw lux conversion | Spectral response, noise, physical optical scene; low-resolution output is idealized |
| PCF8574 | Address selection, power-on HIGH latch, byte writes, reads combining latch and external input mask | Interrupt output, drive current, electrical rise times |

ADS1115 input voltages are limited to 0–5 V in this nominal 5 V workspace; a
configured +/-6.144 V full-scale range does not permit out-of-supply inputs.
Servo output is pulse-to-command mapping, with no shaft mechanics or load.
Buzzer output reports captured GPIO frequency rather than synthesizing audio.
LED indicators show GPIO state rather than diode current/brightness.

I2C uses AVR TWI byte callbacks. Transactions are observable, but do not produce
physical SDA/SCL bit waveforms. GPIO captures still support existing analysis.
Analog circuits remain in the native ngspice workspace; this release does not
provide general MCU/analog feedback co-simulation or arbitrary breadboard nets.

## Capability audit

`GET /api/projects/capabilities` audits all 363 existing catalogue records, including
core tools/boards and imported visuals. It distinguishes behavioral models,
executable/experimental boards, ngspice parts, working tools and no-model artwork.
Chip-name matches link compatible artwork to the chip model, not full breakout
board emulation. The audit is exportable and searchable. Unsupported items never
enter the executable picker. There is no claim that all imported parts work.

`POST /api/projects/run` accepts `{ "project": ..., "source": "..." }` or a
precompiled `hex` field instead of source. Wiring validation happens before
compilation. Host/origin checks and bounded subprocess execution remain enforced.

## Primary references

- TI ADS1115 SBAS444E register map, MUX/PGA, OS status and data rates:
  https://www.ti.com/lit/ds/symlink/ads1115.pdf
- ROHM BH1750FVI manufacturer datasheet, Rev. D (manufacturer-authored copy):
  https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/hat/BH1750FVI.pdf
- NXP PCF8574/PCF8574A Rev. 5 latch and quasi-bidirectional port behavior:
  https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf

Models are bounded protocol/behavioral implementations derived from these device
interfaces. The cited documents are references, not redistributed assets.

## Verification on 2026-10-23

71 Python tests, 16 Node tests, and three browser suites passed: practical
workspace, existing upstream integration, and component library. The practical
suite compiles/runs shared-bus firmware, confirms scheduled button-to-LED feedback,
checks ADS1115 output, saved project state, result export and address conflict
rejection. Four shipped experiments execute in backend tests. A focused ADC
regression checks that configuration changes during a pending conversion do not
alter its sampled configuration. Tests are internal behavioral/protocol checks,
not comparisons against physical instruments or competing simulators.
