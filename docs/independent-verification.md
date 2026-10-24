# Independent verification audit — 2026-10-24

This audit checks executable behavior and numerical accuracy against independent equations. It does not certify perfect operation for arbitrary projects or physical hardware.

## Published baseline

The tested baseline is commit `40f3143a4d9d600304a392b82e951a061bee49ff`. Both GitHub Actions complete-verification runs succeeded, as did the two MPU-6050 smoke runs and the fresh-screenshot workflow. A new local audit nevertheless found an additional valid-input failure, illustrating why green regression tests are insufficient for a blanket correctness claim.

## Failure found and corrected

On ngspice 42, `ac dec 1 1720.75273802 17207.5273802` and `ac dec 40 1000 1000.001` both stall with an infinite reference frequency when the native logarithmic grid degenerates. The application already terminates the subprocess after 15 seconds, but these valid sweeps should complete. The new regression first failed with two timeout errors in 30.119 seconds. It passes after the fix.

When the requested logarithmic grid has fewer than two intervals, the application now uses three linearly spaced samples, retaining both requested endpoints. This is disclosed in `sampling` and the visible measurement note. Ranges that collapse at the solver's input precision are rejected explicitly. Other AC grids retain the native logarithmic analysis. Independent review also caught narrow-frequency rounding in the solver output: regression tests first reproduced duplicate returned frequencies, then passed after selecting 15-digit output and rejecting non-increasing AC axes. This is a bounded integration workaround; it does not alter the engine's equations or silently claim that the requested logarithmic density was preserved. See `evidence/ac-sweep-regression.json` and `UniversityTests.test_sparse_and_narrow_ac_sweeps_have_real_endpoints`.

## Independent numerical oracles

`tests/test_independent_numerics.py` uses seed **20261024** and invokes the real native ngspice executable for **110 circuit cases**:

| Cases | Independent expected result |
| --- | --- |
| 30 unequal dividers, both polarities | Ohm's law, source-current sign, divider voltage and power conservation |
| 20 five-resistor bridges | Two-node conductance equations solved with a 2×2 determinant; KCL at both nodes |
| 40 series RLC networks | Complex impedance, real/imaginary voltage and current, resistor average power and total real-power conservation |
| 20 RC charging circuits | Every useful transient sample compared with the analytical exponential |

The report records **440 point comparisons**, per-case tolerances and all RC full-scale errors. References are calculated independently of the application's netlist/result generation. The audit also deliberately points the application to an absent native executable and requires failure, confirming that numerical success cannot be produced by a hidden fallback or cached formula when the engine is unavailable. These tests use ideal passive-network equations; they do not validate semiconductor parameter sets against manufactured devices.

## Browser engine and end-to-end paths

The actual compiled CircuitJS browser engine is checked against an independent RC charging exponential at two resistance values, sampled deterministically at half a time constant to prevent a settled waveform from passing as a transient check. Its clock must advance when running and remain unchanged when stopped. `evidence/circuitjs-runtime.json` stores sampled time, measured capacitor voltage, expected voltage, error and tolerance. A separate 10 V divider must calculate 5 V and 5 mA. All 373 bundled example files are imported with parser/runtime-error detection and finite electrical-output checks. This catalog check is still smoke testing, not numerical validation of every example, FFT tool or interactive feature.

The complete matrix also exercises native compilation and AVR firmware execution, sensor/protocol models, all 19 university reference experiments, editing/undo/import/export, stale-result removal, invalid inputs, mobile width and the original workspaces. Run `npm run test:all`; `evidence/full-verification.json` records exact commands, exit codes, dependency availability and the tested source fingerprint. CI retains the complete `evidence/` directory and logs. Summary parsing is also tested with ANSI-colored output so that upstream Vitest tests remain counted consistently.

## Remaining limits

No physical hardware, public-hosting load, live online library installation or Windows/macOS installer validation is established by this audit. General MCU/analog co-simulation, ESP32/STM32/PIC full firmware execution and PCB routing remain unimplemented. Current/power output in the university laboratory covers two-terminal branches; multi-terminal device pin measurements are not exposed. These boundaries remain explicit even when all automated checks pass.
