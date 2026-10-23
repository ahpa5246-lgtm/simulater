# Working Workbench Implementation Plan

Goal: deliver an executable schematic-to-measurement milestone and an actual screenshot.
Architecture: local Python HTTP service invokes ngspice in isolated temporary directories; browser SVG editor owns project state and emits a validated graph. No accounts or cloud dependency.
Spec: ../specs/2026-10-23-electronics-workbench-design.md
Execution: native in this session, per owner instruction to build now.

## Constraints and review focus
Full-suite features remain a roadmap. Missing engines produce explicit errors. Import validates schema and resource limits. All computed traces derive from ngspice, never decorative signals. Local service binds loopback and rejects cross-origin writes. Fixed temporary filenames prevent user paths from reaching the solver.

## Task 1: Circuit graph and ngspice adapter
Files: circuit.py, tests/test_circuit.py. Interface: validate(project), netlist(project), simulate(project) returns time/traces/dc/engine.
- [x] Write tests for resistor divider, RC time constant, ground connectivity, floating network, invalid values and command injection.
- [x] Run failing tests, implement schema/net compiler and bounded ngspice runner, rerun tests.

## Task 2: Local workbench
Files: server.py, web/index.html, web/style.css, web/app.js. Interfaces: POST /api/simulate with versioned project JSON; static frontend.
- [x] Exercise browser flow for run, component edit, undo, wire, placement, delete, save/reload and invalid import.
- [x] Implement compact docked schematic, library, inspector, waveform viewer, examples, local persistence and SPICE download.
- [x] Run browser tests and inspect screenshot; correct observed failures.

## Task 3: Review and deliver
Files: README.md, THIRD_PARTY.md, docs/coverage.md, screenshots/workbench.png.
- [x] Run complete Python and browser checks, inspect actual screenshot and fix important findings.
- [x] Document exact implemented scope, setup, dependencies and remaining limitations.
- [x] Commit feature branch; preserve actual screenshot as deliverable.

## Execution record
All three tasks completed for this milestone. Native execution was selected from the owner’s explicit request to build immediately. The full-suite target remains open, as documented in docs/coverage.md. External ngspice is not bundled in git. Final review found import/export injection and missing pin-disconnect recovery; both were corrected and exercised in the browser suite.
