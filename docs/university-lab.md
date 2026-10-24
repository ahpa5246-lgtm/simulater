# University laboratory and CircuitJS — 2026-10-24

Open `/university.html` for the native ngspice laboratory, or `/circuitjs/circuitjs.html` for the bundled CircuitJS editor. Links are present in all three original workspaces. The engines have distinct circuit formats and execution loops; this integration does not create MCU/analog co-simulation.

## Implemented laboratory

| Experiments | Mathematical reference |
| --- | --- |
| Ohm's law; series/parallel resistors; unloaded/loaded divider | Resistance networks, KCL, signed source current and absorbed power |
| Divider DC sweep; resistor current sweep | Linear transfer over a bounded source range, including negative/descending sweeps |
| RC low/high-pass; RL low/high-pass | −3.0103 dB and ±45° at the calculated cutoff frequency |
| Sinusoidal resistor power | Peak-voltage phasor convention: Pavg=Vpeak²/(2R) |
| Transient divider | Time-domain transfer ratio |
| RC charge; RL current step | Exponential response at one time constant |
| Zener regulator; half-wave rectifier | Model-appropriate voltage ranges, not manufacturer qualification |
| Inverting op-amp; saturated NPN switch | Closed-loop gain including finite open-loop gain; saturation voltage tolerance |

There are 19 wired projects. Component values, analysis settings and the complete project JSON are editable. Native OP, transient, AC and DC results expose node voltage, two-terminal branch current and power. AC additionally returns real/imaginary phasors, gain and phase; its power is average real power. Multi-terminal device pin currents/power are not exposed in this laboratory. Reference checks apply only to the unmodified reference project/settings. Editing clears results; invalid or unapplied edits block execution and stale exports. Download `.mina`, full result JSON or the selected measurement quantity as CSV. Plots support cursor inspection and trace visibility through uPlot. Descending sweeps are reversed only for plotting, preserving solver/CSV sweep order.

## Reused CircuitJS engine

Pinned upstream: [pfalstad/circuitjs1](https://github.com/pfalstad/circuitjs1/tree/778723096a46f3c5ce4e11bd9edc24324754f02c). Its TypeScript port registers 148 element classes, including graphical/measurement elements and component variants, and ships 373 example files, including one blank template. This count is not 148 manufacturer-validated chips. The editor includes switches, sources, semiconductors, amplifiers, digital gates/registers, transformers/transmission lines, motors, scopes, FFT and trigger facilities supplied by upstream.

`third_party/circuitjs/source.tar.gz` preserves the exact source commit. `COPYING.txt` preserves GPL-2.0-or-later; source-file notices remain in the archive. `manifest.json` records the archive and every served asset SHA-256. `python scripts/vendor-circuitjs.py` extracts the source, installs its locked build dependencies, applies the documented local integration changes and rebuilds the offline assets. Changes remove the external Dropbox loader/menu, unconfigured short-URL service, deployment-specific manifest/service worker, and add a return link. Solver equations remain unchanged. Source is also downloadable at `/api/circuitjs/source`; integration modifications are in the build script.

`python scripts/test-circuitjs-upstream.py` verifies all asset/source hashes and executes all six upstream test files (60 tests) using the pinned root Vitest/lz-string dependencies. No network installation occurs during verification. The separate browser check imports every example and checks for parse/runtime errors and finite electrical outputs; annotations have no electrical terminals and are excluded from voltage measurement. A 10 V divider is numerically checked for 5 V and 5 mA. Catalog smoke results are in `evidence/circuitjs-catalog.json`. Import checks do **not** validate every example's physical accuracy, every interactive tool, steady-state behavior or external input workflows.

## Review and validation

The complete matrix is run by `npm run test:all`; exact counts, commands, source fingerprint and logs are recorded in `evidence/full-verification.json`. New browser tests exercise all 19 laboratory experiments, plots, parameter edits, disabled grading, CSV/JSON downloads, rejected JSON, empty fields, descending sweep data, mobile width and same-origin writes. Independent review identified and corrected huge-integer validation overflow, stale successful results after invalid edits, nontransactional JSON application, and descending-axis plotting.

This is a substantial circuit/education expansion, not a statement of complete Proteus or Wokwi parity. ESP32/STM32/PIC full firmware execution, general mixed-engine MCU/analog feedback, PCB routing, physical measurement validation and a tested Windows installer remain outside the implemented scope. CircuitJS and native ngspice differ in model assumptions; separate-engine agreement is not automatically guaranteed.
