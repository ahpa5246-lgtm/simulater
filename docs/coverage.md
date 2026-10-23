# Historical analog milestone coverage

For the newer board/sensor milestone and current MCU/library support, see [boards-delivery.md](boards-delivery.md). The remaining gaps below describe the earlier analog-only milestone.

# Delivered coverage — 2026-10-23

## Implemented and exercised

Local browser workbench backed by a loopback Python service and an external ngspice executable. Editing, source properties, pin wiring/disconnection, drag/rotate/delete, undo/redo, example selection, local persistence, file import/download, netlist export, DC operating-point and transient calculations, and voltage plotting are implemented. The component palette contains R/C/L, a fixed generic diode model, and DC/sine/pulse voltage sources. No remote code/fonts/assets are used by the application.

Actual numerical evidence: a 10 V equal-resistance divider measures 5 V; changing the lower resistor to 2 kΩ measures approximately 6.667 V; a 1 kΩ / 1 µF charging circuit reaches the analytical one-time-constant value within 0.03 V. The browser renders genuine ngspice output, not precomputed illustrative sine waves.

## Verification

- `python -m unittest discover -s tests -v`: 17 checks, covering numerical benchmarks, injection, floating nodes, invalid values, duplicate identifiers, time-step limits, wire/net consistency, static file allowlist, HTTP API, origin and Host restrictions.
- `node --check web/app.js`: JavaScript parses.
- `node tests/browser.cjs` with Playwright 1.51.1: real simulations, property edit, undo, persistence, RC output, viewport fit, rejected malicious import and pin disconnect. No page errors observed.
- `screenshots/workbench.png`: actual Chromium screenshot after running the RC example.
- Tested locally on Linux with Python 3.12, ngspice 42 and Chromium 134. Native Windows packaging and end-to-end Windows use have not been verified.

## Review corrections

1. Enforced agreement between displayed wires and simulated node names.
2. Preserved ground during net merging; node rename updates the full connected net.
3. Corrected viewport overflow and independently scrollable side panels.
4. Rejected untrusted source waveform/frequency values before project import and export.
5. Added a per-pin disconnect action so accidental wiring can be repaired without undoing unrelated edits.
6. Restricted local HTTP Host headers in addition to Origin checks.

## Remaining full-suite gaps

Every PCB, MCU/firmware-debug, protocol-analyser, visual-programming and IoT requirement remains unimplemented. The waveform viewer is not a full triggered oscilloscope. AC sweep and other advanced analyses remain unimplemented. KiCad, AVR8js and Verilator were evaluated as candidates but are not integrated. There is no Proteus project-file compatibility or verified 100% interface/behavior parity.

The frontend is a first functional workbench, not a pixel clone of Proteus. Formal visual comparison gates against released competitors remain pending; no claim of comparable visual quality or release readiness is made. The server is intended only for local use, not public multi-user hosting. Wire routing is automatic orthogonal drawing with endpoint references, not a professional interactive autorouter. Imported projects and model complexity are bounded but this is not an OS-level solver sandbox.
