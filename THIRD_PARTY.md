# Third-party foundations

## ngspice

- Project: https://ngspice.sourceforge.io/
- Source: https://github.com/ngspice/ngspice
- Adapter: invokes an independently installed executable; no ngspice binary or source is committed.
- Tested engine: ngspice 42, Ubuntu package `42+ds-3build1` (Linux x86_64).
- Licensing: upstream includes modified BSD terms and component-specific notices; audit the exact distribution and models before bundling. See https://github.com/ngspice/ngspice/blob/master/COPYING.
- This application generates its own netlists and a generic diode model declaration. It does not extract models from Proteus.

## Playwright

- Project: https://github.com/microsoft/playwright
- Used for development browser verification and screenshots, not application runtime.
- Version tested: 1.51.1; Apache-2.0. Browser distributions have separate third-party notices.

## Other evaluated projects

KiCad and Verilator remain architectural candidates and are not integrated. AVR8js and RP2040js are now runtime dependencies as described below. Interface icons and schematic symbols are original SVG/text primitives; no remote fonts or image assets are loaded.


## AVR8js 0.21.0 and RP2040js 1.3.3

Pinned npm runtime dependencies; install with npm ci. Projects: https://github.com/wokwi/avr8js and https://github.com/wokwi/rp2040js. Both distributions declare MIT licensing and retain their LICENSE files under node_modules. These are CPU/peripheral engines, not the entire Wokwi product. The Pico demo machine instructions in boards/pico.cjs are original to this project.

## External Arduino AVR toolchain and core

Sketch compilation invokes externally installed GNU AVR GCC/binutils, avr-libc and ArduinoCore-avr. Tested core: Debian/Ubuntu arduino-core-avr 1.8.6+dfsg-1; GCC 7.3.0. Upstream: https://github.com/arduino/ArduinoCore-avr. These components have their own licenses, including GPL/LGPL terms and applicable runtime exceptions; consult the exact installation's notices before bundling or distributing compiled artifacts. No compiler/core binaries or sources are committed here. The example DoubleADC package includes its own MIT notice; that does not assign a license to the entire application.

## Original component artwork

`web/parts/*.svg` and `catalog.json` are original CC0 illustrations generated locally, not copied from Fritzing. See `web/parts/LICENSE.txt` and `docs/component-art.md`.

## v0.5 integrations

- Wokwi Elements 1.9.2 and bundled Lit dependencies: preserved licenses in web/vendor; presentation only unless an explicit adapter is connected.
- PICSimLab DS1621 and peripheral I²C source: third_party/picsimlab, GPL-2.0-or-later, Luis Claudio Gambôa Lopes. Original notices and COPYING preserved; adapted peripheral-only frontend.
- sigrok Python SPI/I²C/UART decoders and common helper: third_party/sigrokdecode, upstream per-file GPL notices and COPYING preserved. Mina decoder runtime GPL-3.0-or-later.
- Renode STM32F103 platform: third_party/renode, Antmicro MIT license preserved.
- Fritzing imported artwork retains its own attribution/license; official Fritzing graphics are CC BY-SA 3.0.
See docs/open-source-integration.md. No blanket MIT grant is made for this combination.

Adafruit BMP085/BMP180 and Adafruit BusIO firmware source packages are included under examples/libraries, with original license/copyright notices, BusIO LICENSE and UPSTREAM.txt links preserved. Used unmodified by the BMP180 reference firmware.
