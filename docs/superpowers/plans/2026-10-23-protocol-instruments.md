# Protocol sensors and measured instruments

Owner requested continued implementation with practical evidence and a broader Arduino sensor/tool palette. Preserve existing AVR/analog/experimental Pico functionality and implement natively without another requirements interview.

- Execute compiled Arduino pulseIn firmware against a triggered HC-SR04 behavioral device on D3/D2. Compare recorded echo pulse width against independent expected 58 microseconds/cm; no-target case must return timeout.
- Add ideal digital button/PIR/reed/IR inputs, NTC10k beta-divider and joystick analog stimuli. Device models declare their physical omissions.
- Capture actual D0–D13 PIN register transitions with CPU-cycle timestamps; compute completed pulse widths, frequency and duty, expose a logic analyser, CSV and VCD export.
- Add executable bundled sketches (ultrasonic, digital input, PWM/servo-style pulses, buzzer) and a verification dashboard that runs actual firmware and displays expected/measured/error/pass outcomes plus firmware hashes.
- Review negative cases: short trigger, missing sensor, bad wiring, invalid input and truncated captures. Add browser journeys for tool export and repeatable verification. Preserve full evidence and actual screenshots.
- Real hardware comparison remains unperformed. Do not call behavioral/timing simulation an acoustic/optical/motor physical solver, and do not call internal reference tests hardware validation.
