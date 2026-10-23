# Electronics workbench — proposed full-suite target

Status: design for owner review; no application implementation or parity claim.
Research date: 2026-10-23. Target repository: ahpa5246-lgtm/simulater (empty at inspection).

## Intent and boundaries

Build a free electronics design and simulation environment for students and electronics developers. Preserve familiar schematic-first desktop workflows. The owner requests the breadth of Proteus, including its tools and interface workflows. Full-suite coverage is the roadmap, not a promise that an initial release contains every feature. Independently implement behavior and original visual assets; do not distribute proprietary binaries, models, libraries, artwork, or documentation.

Assumptions for review: Windows-first desktop, offline project editing and local simulation, no compulsory account, no paid runtime service. No hosting or deployment is authorized by this document. Optional external tools and models must have explicit provenance and redistribution review. Compatibility with Proteus project formats is unverified and not promised.

## Research basis

Official feature sources, consulted on the research date:

- https://www.labcenter.com/schematic/ — capture, libraries, variants, BOM, explorer, notes.
- https://www.labcenter.com/pcb/ — PCB workflow and board tools.
- https://www.labcenter.com/simulation/ — mixed-signal and embedded co-simulation.
- https://www.labcenter.com/instruments/ — measurement and protocol tools.
- https://www.labcenter.com/microprocessors/ — advertised processor families and MicroPython.
- https://www.labcenter.com/peripherals/ — peripheral models.
- https://www.labcenter.com/visualdesigner/ — flowchart programming.
- https://www.labcenter.com/iotbuilder/ — remote panels and hardware deployment workflow.
- https://www.labcenter.com/ — current advertised additions, including HDI, output jobs and AI tools.

These pages establish categories, not an exhaustive inventory of every command, supported part, package entitlement, shortcut or behavioral edge case. Public documentation has not been checked against a locally running licensed Proteus installation. Pixel parity and numerical parity remain unverified.

## Feature inventory and acceptance obligations

Every item below is PLANNED / NOT IMPLEMENTED. Each broad row requires finer device/command coverage before a parity percentage is meaningful.

| ID | Capability | Required evidence before completion |
|---|---|---|
| CAP-01 | Project creation, open/save, recent projects, recovery, print/export | Round trip without connectivity or property loss; interrupted-save recovery |
| CAP-02 | Component search, categories, preview, placement, duplication, rotation, mirroring | Pin coordinates and instance identity remain correct through transforms |
| CAP-03 | Wire routing, junctions, labels, power nets, buses, ports | Crossing versus connected-wire fixtures produce correct netlists |
| CAP-04 | Select, move, block edit, clipboard, undo/redo, zoom, pan, grid, annotation | Deterministic undo and redo of complete editing sessions |
| CAP-05 | Hierarchical sheets, reusable design clips and cross probing | Repeated subsheets do not accidentally merge local nets |
| CAP-06 | Symbol, footprint and model editors; imports; managed libraries | Versioned provenance, pin mapping checks and missing-model diagnostics |
| CAP-07 | BOM, assembly variants, design explorer, project notes | Outputs reflect fitted parts, alternative parts and current project revision |
| SIM-01 | Operating point, DC sweep, transient and AC analysis | Analytical benchmarks and pinned solver outputs within declared tolerances |
| SIM-02 | Digital events and analog/digital boundaries | Threshold, impedance, unknown-state and feedback timing fixtures |
| SIM-03 | Advanced graph analyses and parameter exploration | Enumerate documented modes individually; unsupported modes stay explicit |
| SIM-04 | Interactive switches, potentiometers, sensors, displays and actuators | Input changes affect simulated electrical state, not only animation |
| SIM-05 | Convergence diagnostics, floating nets, invalid models, cancellation | Actionable errors; UI remains usable; no fabricated waveforms |
| INS-01 | Four-channel scope, XY, coupling, triggers, cursors and live probes | Known signals reproduce amplitude, period, phase and trigger behavior |
| INS-02 | Logic analyser, bus views and trigger conditions | Known digital traces decode with correct timestamps and channels |
| INS-03 | Signal and pattern generators | Measured output matches configured waveform, frequency and duty cycle |
| INS-04 | AC/DC meters, current, RMS, power and counter/timer | Loading and sign conventions documented and benchmarked |
| INS-05 | UART terminal; I2C, SPI and CAN analysis/stimulation | Golden traces, framing errors, ACK/NACK, bus modes and timing checks |
| MCU-01 | AVR execution with timers, interrupts, GPIO, UART, SPI, I2C and ADC | Firmware fixtures verify each implemented peripheral and pin mapping |
| MCU-02 | ARM, PIC/dsPIC, 8051, MSP430 and other advertised families | Exact part support matrix; unsupported devices cannot run deceptively |
| MCU-03 | ELF/HEX loading, source debug, breakpoints, stepping, registers and watches | Source/symbol mapping and reproducible halt/resume behavior |
| MCU-04 | Compiler/IDE integrations, MicroPython and supported board workflows | Real toolchain output executes on the declared model; limitations visible |
| PCB-01 | Footprint association, schematic synchronization, board outline and placement | Net and pin identities survive forward/back annotation |
| PCB-02 | Layers, track/via rules, interactive routing, push/shove and autorouting | Clearance/width constraints and unconnected-net reporting |
| PCB-03 | Copper fills, thermal relief, teardrops and design-rule checking | Geometric fixtures and independent output inspection |
| PCB-04 | Differential pairs, length tuning, stackups, blind/buried/microvias and HDI | Per-feature geometric and rule tests; unsupported stackups rejected |
| PCB-05 | 3D board view and mechanical interchange | Board dimensions and footprint transforms verified against PCB data |
| PCB-06 | Gerber, drill, placement, BOM and other manufacturing formats | Separate format-specific acceptance; external viewer/import validation |
| PCB-07 | Grouping, precise measurement/move and output jobs | Repeatable transforms and revision-consistent output bundles |
| VIS-01 | Flowchart editor, code generation, peripheral gallery and debugging | Generated firmware follows branches, loops and timing fixtures |
| IOT-01 | Front-panel editor, control binding, simulated and hardware connections | Correct state synchronization, disconnect handling and explicit permissions |
| EDU-01 | Examples, tutorials and robot/teaching workflows | Examples actually execute and disclose idealized physical assumptions |
| AI-01 | Optional assistant and datasheet-assisted part creation | Never compulsory; generated pinouts/models require review and validation |

## Architecture and alternatives

Recommended direction: a local desktop workbench with independent editor, circuit graph, model catalogue, solver adapter, event scheduler, instrumentation and project-format modules. Simulation runs outside the UI thread. Numerical engine failure must not corrupt the project. Only a versioned circuit graph can produce a simulation netlist; screen coordinates never serve as connectivity.

Candidate foundations:

1. ngspice for analog and supported mixed-signal analyses. Inspect exact source revision, build options, model licenses and API behavior before adoption. Reference: https://ngspice.sourceforge.io/docs.html
2. AVR8js for an initial supported AVR target, not as a universal microcontroller engine. Its README states MIT licensing. Reference: https://github.com/wokwi/avr8js
3. KiCad integration or a licensed KiCad-derived PCB subsystem is preferable to casually rebuilding a professional router. First prove actual import/export and automation boundaries. Its existing SPICE and PCB workflows are also comparison references: https://www.kicad.org/discover/spice/ and https://www.kicad.org/discover/pcb-design/
4. Verilator is a candidate for compiled HDL models, not a replacement for analog SPICE or every digital timing model. Reference: https://veripool.org/guide/latest/overview.html

Alternative A: extend an established EDA application. This reuses mature schematic/PCB behavior but creates a larger upstream maintenance and licensing commitment. Alternative B: browser-only application. Distribution is convenient, but solver packaging, local toolchains and offline firmware/debug support require feasibility work. Decide the PCB reuse boundary before writing a custom PCB editor.

Co-simulation contract: monotonic simulation time, deterministic event ordering, declared logic thresholds and drive impedances, feedback handling and bounded stepping. An emulator and a SPICE engine are not integrated merely because both run. Test PWM through an RC filter and ADC feedback before expanding processor coverage.

Project ownership: local files belong to the user. Versioned schema, stable component/pin/net identifiers, migration backups and atomic saves. Waveforms are derived data tied to a project hash, engine version, model revisions and simulation settings. Editing invalidates stale results visibly.

Security boundaries: imported projects, model files and firmware are untrusted; cap resource use and execution time, restrict include paths, prevent implicit arbitrary commands or remote fetches, and require explicit user action for hardware/network access. Compile and simulation errors must be recoverable.

## Interface direction

Use a compact desktop workbench: command menus and toolbars; left component/mode panel; central schematic; dockable properties, results and logs; persistent run/pause/stop controls and simulation status. Separate destinations for PCB, firmware and library work. Prefer task-specific tools to one overloaded canvas. Original icons and branding; readable sizing and keyboard focus; tooltips and shortcut discovery.

Compare two composition options before implementation: a traditional dense engineering workspace and the same command model with collapsible contextual panels. Compare actual released Proteus and KiCad workflows plus a third released engineering UI reference. Official pages were researched; visual review with comparable screenshots is still pending. No aesthetic superiority claim is supported yet.

## Delivery sequence without deleting full-suite scope

1. Prove native solver packaging, PCB reuse boundaries, and circuit graph invariants.
2. Complete schematic → netlist → DC/transient → measurements → save/reopen.
3. Add interactive digital and AVR execution, then demonstrate electrical co-simulation.
4. Complete instruments, debugging, analyses and device-specific coverage incrementally.
5. Integrate PCB workflows and independently validate manufacturing output.
6. Add visual programming, IoT, teaching and optional assistant capabilities.

Each stage ends in tested user outcomes, a coverage ledger, known limitations and review corrections. No decorative tool is counted as implemented.

## Self-review and corrections

- Initial proposal undercounted PCB, debug, protocol, visual programming, IoT and library tooling. Expanded the inventory above.
- Initial ngspice + AVR framing could suggest instant co-simulation. Added an explicit scheduler and electrical boundary acceptance gate.
- A tiny custom PCB router would not justify parity claims. Added mature-tool reuse evaluation before PCB implementation.
- Public marketing pages cannot prove exhaustive feature or command coverage. Added explicit source and installation-access limitations.
- A parity percentage over broad categories would mislead. Require per-command/per-device inventory and reproducible tests first.
- Merely loading a firmware file does not prove MCU support. Added per-peripheral and source-debug checks.
- Clean screenshots cannot prove simulation. Added analytical, numerical, trace and manufacturing validation requirements.

## Review decision needed

Review this written specification and correct the desktop/offline assumptions or feature scope. No implementation plan has been approved, no source dependencies have been adopted, no application tests have run, and nothing has been deployed. Exact version pinning, license audit, complete device catalogue, visual comparisons and executable feasibility probes remain implementation-planning prerequisites.
