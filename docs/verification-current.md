# Simulator verification — 2026-10-24

This is a regression verification record, not a certificate that every possible circuit or every Proteus feature works. The machine-readable [report](../evidence/full-verification.json) identifies the exact tested source fingerprint, base commit, dependency availability, commands and exit codes. Reproduce it with `npm ci`, a configured ngspice/AVR toolchain, Playwright Chromium, and `npm run test:all`.

## Result

The current full local matrix passed **173 tests (93 Python, 20 Node, 60 pinned upstream CircuitJS)** and **all ten browser suites**, with no skipped tests and a stable source fingerprint. Total duration: **79.555 seconds**. Exact commands, exit codes and the tested fingerprint are in `evidence/full-verification.json`.

Version 0.7 adds 19 native ngspice university experiments with OP/transient/AC/DC, current/power and Bode plots; all original reference checks pass. It also bundles the pinned GPL CircuitJS engine, 148 registered element classes (including variants/graphics) and 373 example files. The example audit checks import, parser/runtime errors and finite electrical outputs; it is not an accuracy certificate for every example/tool. A CircuitJS divider is independently checked at 5 V / 5 mA. [New laboratory scope and source provenance](university-lab.md).

Independent review found and corrected four defects in the new work: huge-integer validation overflow, stale PASS/results after invalid component edits, failed JSON import committing invalid active state, and descending DC axes passed directly to uPlot. Added regressions cover these cases. The earlier amplifier/component audit below remains applicable. The current evidence is local; hosted CI is a separate check.

## Implemented and exercised

| Area | What the checks actually exercise |
| --- | --- |
| Native analog solver | DC operating point and transient results; divider voltage, RC time constant, finite reference results for every one of the 39 presets |
| New electrical behavior | Current-source Ohm's law; NPN/MOSFET load switching; amplifier closed-loop gain and clipping; 24 AND/NAND/OR/NOR/XOR/XNOR truth-table cases; potentiometer ratio; Zener breakdown; LED forward curves; controlled sources and switch control |
| Schematic editor | Search, placement, multi-terminal wiring and rotation, terminal edits, delete/undo, persistence, project import/rejection, gallery placement, backend-generated SPICE export, waveform consistency, viewport height |
| AVR firmware | Compile real C++ and ZIP libraries; execute Uno/classic Nano HEX; scheduled ADC/button changes, UART, pulse measurement, servo command and shared I²C bus examples |
| Sensors | Existing analog/digital inputs and I²C models, including the MPU-6050 register model; disconnection/address conflicts and invalid inputs are tested |
| Instruments/integrations | GPIO measurements, VCD and execution export, bundled sigrok decoder logic, native PICSimLab register adapters, Fritzing sanitization/import and Renode profile export |
| Artwork | 35 original illustrations, 50 Wokwi visual elements, 278 credited community SVGs; artwork availability is not firmware/device support |
| Regression infrastructure | Every discovered Python/Node test, pinned upstream CircuitJS tests and ten browser suites run; failures preserve logs and return nonzero. Source edits during the matrix invalidate its success claim. |

## Added executable options

The analog palette expanded from six entries to **39 presets**, including waveform and parameter variants. These are not 39 independent manufacturer-validated chip models.

| Group | Presets |
| --- | ---: |
| R, C, L | 3 |
| DC/sine/pulse voltage and current sources | 6 |
| Silicon, Schottky, three Zener voltages and four LED variants | 9 |
| NPN/PNP, NMOS/PMOS, N/P JFET | 6 |
| Controlled voltage/current source and voltage-controlled switch | 3 |
| Ideal amplifier and comparator | 2 |
| AND, NAND, OR, NOR, XOR, XNOR, buffer, inverter | 8 |
| Potentiometer and diode bridge | 2 |

All presets have explicit terminals and local trusted SPICE templates. External user-supplied models/expressions are not accepted. Every reference circuit is selectable in the example menu, editable, wired, executable and exportable. Native ngspice provides the device equations; original generic parameter sets are described in `analog_parts.py` and the [upstream manual](https://ngspice.sourceforge.io/docs/ngspice-html-manual/manual.xhtml).

The existing practical firmware workspace retains 21 behavioral/output model types. Its MCU and sensor models do not automatically connect to the analog solver. The 363-record illustration/tool/board audit remains separate; it now correctly links Wokwi MPU-6050 artwork to the executable IMU model and reports the 39 analog presets separately.

## Defects corrected during this audit

- Refreshed desktop layout exceeded the viewport and clipped the workbench/status area.
- Old gallery aliases stopped selecting diode/voltage-source entries after palette expansion.
- MPU-6050 appeared as artwork-only in the capability audit despite its executable model.
- SPICE export used a separate two-terminal-only frontend generator; it now shares execution's validated multi-terminal backend.
- Imported source profiles could display a DC symbol/control while the solver selected the profile's sine waveform; frontend/backend defaults now agree. Explicit null profiles are rejected during import.
- The illustration browser test counted cards from another hidden dialog. It now scopes its assertions to the illustration gallery.
- A second CI invocation exposed an asynchronous import assertion race in the new browser test. The test now waits for the actual import result instead of sampling the previous status.
- The optional CLI browser test assumed an installed binary; it now checks either real status or the real unavailable diagnostic. Live online installation remains unverified.

## Accuracy and remaining gaps

Generic educational diode/transistor parameters have not been compared with physical samples or vendor models. Logic gates have ideal thresholds and no propagation delay/fanout model. Amplifiers/comparators have ideal gain and near-ideal rail clamps (independent review found less than 0.1 mV rail overshoot), without bandwidth/slew/current-limit modeling. Potentiometers clamp endpoint segment resistance to 1 µΩ. I²C uses byte-level transactions, not electrical SDA/SCL waveforms; servo output is pulse-to-command mapping without mechanical load or torque.

Regression success does **not** verify live Arduino CLI registry search/download/install. The report records whether the actual CLI binary is available; local ZIP-library installation/compilation and bounded CLI subprocess/error handling are exercised separately. Renode tests export profiles, not STM32 execution. RP2040 execution remains the documented experimental single-core application subset.

Still unavailable: ESP32/STM32/PIC/Raspberry Pi Linux execution, general MCU/analog feedback co-simulation, PCB routing/manufacturing/3D, MCU source debugger, AC sweep, arbitrary model import and Proteus file compatibility. Windows/macOS/native installer, public hosting and physical hardware upload are not verified.

Proteus' defining capability includes interaction between real MCU machine-code execution and connected analog/digital electronics ([official description](https://www.labcenter.com/simulation/)). This project has not reached that general co-simulation scope. A larger visual library or this passing regression matrix is not evidence of Proteus parity.
