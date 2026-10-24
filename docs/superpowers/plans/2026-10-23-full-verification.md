# Executable components and full verification implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Exercise every existing test suite, fix reproduced failures, and expand executable circuit models rather than count visual assets as simulation.

**Architecture:** Retain native ngspice, AVR8js, RP2040js, PICSimLab and sigrok. A bundled, explicit analog registry drives both schematic pins and validated SPICE generation. Extend the existing editor without changing saved two-terminal project compatibility.

**Tech Stack:** Python standard library, ngspice, Node.js, Playwright.

**Spec:** Existing electronics-workbench design plus this request: test all exposed features, add executable components, report real limitations against Proteus. Implementation choices below are the implementer's choices.

## Global constraints

- Keep loopback/origin checks and bounded solver/compiler execution.
- No proprietary Proteus code/assets or unverified manufacturer-model claims.
- Existing `.mina` projects remain valid; visual imports never imply electrical support.
- No claim of physical validation or complete Proteus parity.

## Review focus

- Missing/unknown model or terminal must fail before invoking ngspice.
- All terminals must participate in node renaming, wires, export and persistence.
- Every advertised analog preset must solve a real test circuit with finite results.
- Missing optional dependencies must be reported, never silently passed.
- Browser suites share a port: run sequentially, collect failures and preserve logs.

### Task 1: Expand the analog solver and typed registry

Files: `analog_parts.py`, `web/analog-parts.json`, `circuit.py`, `tests/test_analog_parts.py`.

Interface: registry records expose `id/type/name/pins/value/unit/model/scope`; `part_for(component)` and `pins_for(component)` validate a component's profile; `spice_line(component)` generates only trusted templates.

- [x] Write failing numerical tests: 1 mA/1 kΩ, NPN and NMOS switches, op-amp gain, logic truth tables, model/type mismatch and missing terminal.
- [x] Implement parameterized models, multi-terminal validation and solver collection.
- [x] Execute a reference fixture for every catalog entry, plus existing circuit tests.

### Task 2: Connect the registry to the schematic editor

Files: `web/app.js`, `web/index.html`, `server.py`, `tests/analog-parts-browser.cjs`.

Interface: serve `/analog-parts.json`; render all pins from registry; `/api/circuit/netlist` uses the same backend exporter as execution.

- [x] Write failing browser tests for placing a transistor, third-terminal edits/wiring, rotate/delete/undo, saved import and solver-backed netlist download.
- [x] Implement searchable palette, multi-terminal symbols, inspector and safe backend export; add circuit examples for new families.
- [x] Run new and existing circuit browser suites.

### Task 3: Reproducible complete verification

Files: `scripts/verify-all.py`, `package.json`, `.github/workflows/verify-all.yml`, `docs/verification-current.md`, `evidence/full-verification.json`.

Interface: `npm run test:all` runs Python, every Node unit suite, every browser suite sequentially, and returns nonzero on any failed check. Report records commands, counts, exit codes, duration and tested source revision.

- [x] Run all current suites; reproduce/fix failures at their cause with regression tests.
- [x] Add missing model coverage checks, run the complete matrix, inspect actual screenshots.
- [x] Publish code and a dated report with explicit unsupported devices and physical-model omissions.

## Completion evidence

`npm run test:all`: 107 tests, eight browser suites, all passed; source stable. Independent review: no Critical finding; reporting gaps addressed with dependency availability and unverified-capability disclosure. Import waveform/null-profile edge cases were corrected with browser regressions.
