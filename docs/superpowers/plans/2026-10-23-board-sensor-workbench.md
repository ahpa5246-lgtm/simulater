# Board, sensor and library milestone

Owner instruction: proceed with a simulator supporting board families already discussed, including Arduino and Raspberry Pi, and installable libraries. Execute natively; no further board-selection interview.

1. Add a real AVR8js adapter with bounded Intel HEX loading, CPU/peripheral execution, ADC sensor input, GPIO transitions and UART output. Support ATmega328P Uno/Nano first; reject other chips explicitly.
2. Add local Arduino AVR sketch compilation using an installed AVR compiler and Arduino AVR core; expose missing-tool diagnostics. Install source libraries from bounded local ZIP archives without executing installer scripts. Compile against their headers/sources. Retain their licensing metadata. SPI/Wire/EEPROM support depends on emulator peripheral coverage, not installation alone.
3. Add a dedicated board workspace with board catalogue, firmware editor/import, sensor controls, simulated wiring, serial monitor and execution evidence. Keep existing analog workbench working.
4. Evaluate a Raspberry Pi Pico adapter using RP2040js; do not conflate Pico with Linux Raspberry Pi boards. Declare unsupported boards/models instead of pretending to execute them.
5. Verify compiled firmware responds to changed sensor inputs; check malformed firmware and archive traversal; run analog and browser regressions; self-review and correct findings. Preserve an actual screenshot and local git commit. GitHub publication remains unapproved following earlier automatic rejection.

Full-suite integration is incremental. This milestone does not establish universal MCU, arbitrary sensor or physical-model accuracy. Source library support does not imply a corresponding electrical sensor model exists. No PCB implementation in this milestone.

## Execution outcome
Implemented AVR execution, Arduino compilation, local source-library installation, sensor controls and a board workspace. Added experimental Pico UF2 application execution with explicit limits. All 31 Python checks, 3 Pico checks and both browser suites passed. Review corrections and remaining board families are recorded in docs/boards-delivery.md. GitHub publication remains blocked/unapproved; no push was attempted.
