# Practical simulation upgrade

Intent: move from artwork browsing and single-sensor presets to editable multi-device firmware projects. Continue on the existing AVR8js engine and native compiler; no fake reading generators.

Approach: add a validated project schema translating explicit device connections into engine configuration; extract I2C bus routing into a module supporting multiple independently addressed devices; retain legacy request compatibility. Add ADS1115 conversion/config/timing, BH1750 measurement commands/timing and PCF8574 latch/external input behavior from manufacturer documentation. Support bounded time-varying GPIO and analog stimuli. Expose an executable-only workspace with saved/imported/exported projects, source compilation, address/pin conflict checks, waveform results and protocol state evidence. Catalogue artwork can only claim compatibility through an explicit model mapping.

Limits: behavioral/protocol simulation, not transistor or optical physics. I2C uses AVR TWI byte callbacks, not electrical SDA/SCL edges. Unsupported catalogue devices remain clearly outside executable selection. No assertion of support for all imported hardware or superiority over other simulators.

Tasks:
- Test multiple I2C address routing, missing-device NACK, address conflicts, conversion timing/configuration, GPIO latch semantics and invalid input rejection.
- Implement bounded behavioral I2C models and bus integration; retain existing firmware regressions.
- Add validated multi-device project translation and stimulus events, test actual compiled Wire/ADC/GPIO firmware with changed/disconnected inputs.
- Add practical project workspace and capability report covering every catalogue record; test browser editing, persistence, compile/run and exports.
- Review failure paths and run complete regression tests. Publish exact tested tree to GitHub.
