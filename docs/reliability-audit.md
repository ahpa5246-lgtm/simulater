# Reliability and open-source audit — 2026-10-24

This audit verifies executable results and records limitations. It does not certify perfect operation for all circuits, firmware, devices, or upstream editor tools.

## Reproduce the evidence

Install the pinned npm dependencies with `npm ci`, configure the native ngspice and AVR toolchain as described in README.md, and install Playwright Chromium. Run `npm run test:all`. The runner discovers every Python test, Node test and `*browser.cjs` suite, runs browsers sequentially, fails on skipped/incomplete suites or source changes, and writes exact commands, exit codes, tool versions and source SHA-256 to `evidence/full-verification.json`. Complete command logs remain in `.state/verification/` and are uploaded by CI.

## Final result

The final local matrix passed **177 tests (97 Python, 20 Node, 60 pinned upstream CircuitJS)** and **12 browser suites** in **142.163 seconds**, with no skipped tests, zero nonzero exit codes and a stable source fingerprint. Ten initial-state accessibility scans report zero automatic violations and retain 14 rule-level incomplete groups for manual review. This is local evidence; hosted CI status is a separate result.

## Coverage and boundaries

| Area | Executable evidence | Boundary |
| --- | --- | --- |
| Native analog editor | 39 preset reference circuits; placement, multi-terminal wiring, rotation, property edits, undo, persistence, import rejection, SPICE export and real waveform output | Generic educational device parameters; no manufacturer/hardware validation |
| Independent numerical audit | 110 seeded cases: unequal dividers, resistive bridges, complex RLC and RC exponentials; 440 point comparisons and 39,520 transient samples | Independent ideal-network equations, not every semiconductor/device configuration |
| University laboratory | All 19 reference experiments; actual OP/transient/AC/DC execution, gain/phase, currents/power, exports, invalid/stale state and modified-circuit grading | Two-terminal branch measurements; reference grading only for original configurations |
| Firmware and devices | Real AVR compilation and Uno/Nano instruction execution, sensor/register/protocol tests, shared I²C, scheduled inputs, disconnected devices, timing and invalid inputs | Byte-level I²C; ideal input/output models; experimental Pico subset; no general MCU/analog feedback co-simulation |
| Instruments and integrations | GPIO timing, VCD/CSV/JSON, sigrok decoder subset, native PICSimLab peripherals, local ZIP libraries, sanitized Fritzing import, Renode profile export | Live Arduino CLI registry operations and actual Renode firmware execution remain unverified |
| CircuitJS | 60 pinned upstream tests; 373 example import/runtime/finite-output smoke checks; independent divider and RC transient checks; start/stop and native text export | Catalog smoke tests do not numerically validate every example, FFT tool, menu option or element |
| Visual/accessibility | Existing visual/browser regressions plus ten axe-core scans: five initial workspace DOMs at desktop/mobile widths; board pin keyboard activation | Embedded upstream editor, dialogs, screen readers, and general keyboard navigation are not certified; incomplete findings require manual review |

Failure without a native ngspice executable is tested explicitly: the application must report an error rather than invent numerical output. Numerical audit values are computed from independent equations rather than the application's result-generation code.

## Defects reproduced and corrected in this audit

The initial full run passed all 177 unit/upstream tests but failed the original schematic browser suite: its unsafe-import assertion sampled the previous simulation status before the asynchronous file read finished. The test now awaits the actual rejection and still requires both an `Invalid` status and the unchanged active circuit. Application validation was not weakened. `evidence/reliability-audit-before.json` retains the failed baseline summary.

A new accessibility audit first failed against the actual site. At desktop width it identified 139 node-level findings across contrast and semantic rules. Corrections darken secondary text within the existing green/mint palette, give the protocol selector a name, expose interactive SVG board pins inside a group rather than an image, and make scrollable records/tables focusable. Palette names now include their visible text; stable data attributes keep artwork and gallery placement independent of accessible-name wording. Simulation equations, compiled firmware engines and device models are unchanged.

## Open-source improvement

The project now uses unmodified Deque **axe-core 4.14.0** as a pinned development dependency, from https://github.com/dequelabs/axe-core. Its MPL-2.0 notice is retained in the npm distribution, its exact artifact integrity is locked, and attribution is recorded in THIRD_PARTY.md. `npm run test:accessibility` runs it separately; the full verifier also discovers it automatically. It runs locally through browser automation with the site's CSP enabled and adds no production script or remote service.

The audit retains both violations and incomplete findings in `evidence/accessibility-audit.json`. Zero automatic violations is a bounded automated result, not a claim that all accessibility requirements pass. Canvas content, clipped content, empty measurement tables and other ambiguous cases require manual assessment. Existing ngspice, CircuitJS, Wokwi CPU/visual engines, PICSimLab, sigrok, Adafruit and uPlot attribution remains intact.

## Unverified or unavailable

Physical device accuracy, hardware upload, Windows/macOS packaging, production hosting/load, live online library installation, arbitrary imported models, broad ESP32/STM32/PIC execution, PCB tools and general mixed MCU/analog co-simulation remain outside the demonstrated result. Further features should arrive with their upstream provenance, executable adapter, meaningful independent checks and explicit limitations.
