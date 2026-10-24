# University workbench and CircuitJS integration

Goal: integrate a complete pinned open-source CircuitJS engine, not pictures, and add native ngspice AC/DC analysis plus university experiments and interactive measurement plots.

Implementation choices: reuse CircuitJS upstream 778723096a46f3c5ce4e11bd9edc24324754f02c with source archive, GPL notice and narrowly documented offline build patches. Retain ngspice/AVR workspaces. Use uPlot 1.6.32 (MIT) for plotted native results. No claim of Proteus/Wokwi parity or flawless support for every hardware device.

## Interfaces

`university.py`: `experiments()` returns list of records: `id`, `title`, `titleAr`, `category`, `objective`, `equation`, `project` (.mina v1), `analysis` (`type`: `op`/`transient`/`ac`/`dc`, and mode settings). `run_experiment(request)` accepts `experiment` id plus optional `project`/`analysis` overrides; returns `experiment`, `result`, `checks` and `referenceUnmodified`. Each check has label/actual/expected/tolerance/passed. Edited projects disable reference grading explicitly.

`analyses.py`: `analyze(project, settings)` returns `mode`, `axis`, `axisLabel`, `traces` (node voltage arrays), `currents`, `power` (if available), and for AC `gainDb`/`phaseDeg`. Preserve native ngspice values and source-current sign. AC settings: source, startHz, stopHz, pointsPerDecade, amplitude. DC: source, start, stop, step. Transient uses project.analysis. Source IDs must name actual V sources; no user SPICE expressions or paths.

`GET /api/university/experiments`; `POST /api/university/run` bind the above. `/university.html` provides experiment picker, editable JSON project, mode controls, solver results, analytical checks, uPlot plots, current/power table, CSV/JSON/project exports and links to existing tools. `/circuitjs/circuitjs.html` serves a complete manifest-allowlisted offline CircuitJS build.

## Work

- [x] Native analysis and experiment registry: numerical tests before implementation, AC RC cutoff/phase, DC divider slope, source current and resistor power, invalid-input bounds, 12+ executable experiments with independent math checks.
- [x] CircuitJS integration: pinned source/build/patch provenance, upstream 60-test suite, allowlisted assets, external Dropbox/service-worker startup disabled, browser numerical/editor/API tests and a full example catalog audit.
- [x] University UI: actual ngspice result plots with uPlot, import/edit/run/export, stale-result clearing, finite error reporting, narrow-screen layout. Browser tests cover each exposed new workflow.
- [x] Complete regression matrix (173 tests + 10 browser suites), independent review and current evidence/limitations.
- [x] Prepared exact tested source tree and evidence for GitHub publication.
