# Board and sensor workbench — verified milestone

The owner prioritized microcontroller boards, sensor simulation and installable libraries over Proteus-specific cloning. This milestone adds actual execution and compilation to the existing analog workbench. It does not complete the full simulator roadmap.

## Actual capabilities

| Target | Delivered | Important boundary |
|---|---|---|
| Uno R3 / classic Nano | AVR8js ATmega328P execution; separate Arduino build definitions; HEX import; GPIO transitions; timers; UART output; ADC inputs | No general source debugger, full device conformance or cross-engine analog co-simulation |
| LM35 / TMP36 | Environmental temperature becomes voltage read by executing firmware | Ideal transfer functions; physical noise and loading omitted |
| Potentiometer / light divider | Configurable 0–5 V analog stimulus | Light is normalized input, not calibrated lux or photocell physics |
| LM75 | Real Arduino Wire library reads a modeled 0x48 temperature register; transaction capture | Temperature-register subset only; no alarms/configuration fidelity |
| Source libraries | Local bounded ZIP install; dependency/header discovery; actual AVR compile and link | No scripts, assembly sources, precompiled packages, automatic sensor-model creation or universal library compatibility |
| Raspberry Pi Pico | RP2040js single-core application-entry UF2 loading; original ARM GPIO25 demo; UART0 capture | Experimental; ROM boot, WFI/WFE, USB serial, dual-core and general SDK/MicroPython compatibility unsupported |
| Pi 4/5, ESP32, STM32, PIC | Visible catalogue status | Not executable; adapters pending |

Library files persist in `.state/libraries`, outside version control. The browser preserves the sketch separately from board preview text. Board changes invalidate results and firmware. Every execution starts a fresh CPU instance; persistent EEPROM between runs is not implemented. Sensor input changes require re-running; this release uses bounded snapshots rather than continuous real-time simulation. Pico and AVR are separate adapters; they are not yet synchronized with ngspice.

## Tests observed

- Python: 31 checks, including the existing analog/API suite, real compiled sensor firmware, Wire LM75 reads, installed-header compilation, Nano board definitions, invalid HEX, archive traversal, source-count limits and compiler file-read rejection.
- Node: 3 Pico checks — actual GPIO toggling, invalid UF2 and rejection of unsupported sleep instead of executing through it.
- Board browser: ADC input changes produce 51 versus 204 in firmware UART output; D13 responds; LM75 returns 30.0 C; a library ZIP installs and its doubleADC header produces 102; Pico firmware executes; selecting Pico preserves Arduino source; stale firmware import is rejected after a board change.
- Analog browser suite: original simulation/edit/undo/persistence/viewport journeys still pass.
- Real screenshots: `screenshots/boards-sensors.png` and `screenshots/workbench.png`.

Test environment: Linux, Python 3.12, Node 24, AVR GCC 7.3.0, Arduino AVR core 1.8.6, AVR8js 0.21.0, RP2040js 1.3.3, ngspice 42 and Chromium 134. Windows compiler discovery/builds remain unverified.

## Review corrections and scope decisions

1. Added preprocessing dependency validation and rejection of assembler `.include`/`.incbin` file reads, including adjacent/escaped strings. Diagnostics are withheld when preprocessing has not passed dependency checks. Added file/CPU/process-time/source-count limits. This is a compiler-input policy, **not an OS sandbox**; the toolchain and installed Arduino core remain trusted and the service remains local-only.
2. Rejected unsupported Pico sleep/WFI/WFE explicitly rather than running instructions while the CPU should be asleep. A future adapter can implement event-aware wait progression.
3. Added firmware-import revision/board checks and execution format checks to prevent a stale HEX/UF2 import from silently running another board's demo.
4. Fixed selecting Pico overwriting the saved Arduino sketch with preview comments.
5. Added Nano-specific build definitions and its analog-input variant instead of compiling every sketch as Uno.

Bundled original example sketches and their compiled HEX files allow simulation without a local AVR compiler; compiling edits still requires the external toolchain. The Pico application demo UF2 is an adapter fixture without boot2 and must not be presented as a complete physical-board boot image.

No remote push or deployment was attempted for this milestone; the earlier publication rejection remains in effect. Source is committed locally on the feature branch. The full exact board/sensor catalogue still needs implementation and validation; no all-devices-supported claim is made.
