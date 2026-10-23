# Open-source integration ledger (v0.5)

This release incorporates reusable components rather than treating a copied repository as a working simulator. It does not include every sensor/board supported by every upstream project, and it has not established superiority or full Proteus parity.

| Source | Integrated capability | Verification / boundary |
| --- | --- | --- |
| Wokwi Elements 1.9.2 (MIT) | All 50 registered elements in this pinned npm bundle, offline searchable gallery, adapters linked to existing sensors/boards; LED and servo command indicators driven by captured execution | All 50 register in browser; unsupported elements remain visual-only. Servo mapping is a command indicator, not mechanics. |
| Arduino CLI (GPL-3.0) | Optional isolated registry search, exact-version installation, status/list APIs and UI | Real 1.5.1 version check; boundary tests. Registry operations encountered environment network/DNS failure; successful installation not verified. CLI-managed libraries remain separate from active ZIP source libraries. |
| PICSimLab (GPL-2.0-or-later) | Native DS1621 and BMP180 register models, unmodified Adafruit BMP085/BMP180 and BusIO source libraries, temperature/threshold/configuration reads and writes, real compiled Wire example | Signed temperature, configuration and disconnected NACK tests. Actual Adafruit driver firmware checks BMP180 at 10/25/40 °C and 900/1013.25/1050 hPa; pressure error tolerance 200 Pa, oversampling 3 only. Compile optional adapter with `python scripts/build-picsimlab.py` after `npm ci`; requires C++ compiler. TWI byte events are mapped to upstream register events; this bypasses bitbang electrical timing. No thermostat/conversion timing claim. |
| sigrok/libsigrokdecode | Unchanged upstream SPI/I²C/UART Python decoders in a bounded separate interpreter, selectable captured channels, report export | SPI A5/3C decoded from executed AVR GPIO writes; independent I²C address/NACK and UART 55 frames. Our API-v3 subset runtime is used, not the complete C libsigrokdecode runtime or protocol stacking. UART UI is 8N1. |
| Fritzing Parts | Local FZPZ import and sanitized SVG visual inventory | See fritzing-import.md. Artwork and connectors do not add an electrical device model. |
| Renode (MIT) | Upstream STM32F103 platform description and local ARM-ELF launch-script exporter | `python scripts/export-renode.py firmware.elf --output session.resc`, then use installed Renode. Export path/ELF guards tested; actual Renode execution is not verified here. Browser STM32 adapter remains pending. |

## Rebuild and tests

`npm ci` installs pinned JS dependencies. `python scripts/vendor-wokwi.py` refreshes the offline Wokwi bundle and dependency licenses. `python scripts/build-picsimlab.py` builds the optional local N-API module. The native binary is platform-specific and deliberately excluded from git; the complete adapter/model source and GPL text are included.

Run Python unittest discovery, Node tests including `tests/test_ds1621.cjs`, and all browser suites. `tests/upstream-browser.cjs` checks the real upstream elements, native model, GPIO-driven servo command and protocol decoder UI. No board upload is performed by these checks.

The existing ngspice, AVR8js and experimental RP2040js adapters remain in use. ESP32, Raspberry Pi Linux and broad STM32/PIC support are not unlocked by installing graphics or compiler cores. Each needs an actual engine adapter and firmware/peripheral validation.

## Licensing and provenance

Upstream notices and license texts accompany vendored code. PICSimLab's peripheral frontend is adapted to omit controller/GUI dependencies; its DS1621 and BMP180 sources remain unchanged. Sigrok decoder sources are unchanged; `boards/decode_worker.py` is our GPL-3.0-or-later subset runtime. Renode's platform file is unchanged. Wokwi/Lit license copies are under `web/vendor`. These notices apply to their respective code, not a blanket permissive relicensing of the combined application. The owner still needs to select an appropriate application license before general redistribution; GPL obligations must be respected for combined/derived works.

## Adafruit firmware libraries

Import `examples/libraries/AdafruitBusIO.zip` and `AdafruitBMP085.zip` through the existing Library manager before recompiling the BMP180 sketch. Bundled HEX runs without library installation, but the native peripheral adapter must be built. Original Adafruit source, copyright comments, license notices and upstream links are retained. The pressure model is approximate: one run at 25 °C and 1013.25 hPa produced 101410 Pa. Library code is not modified to manufacture the expected reading.

Native peripheral build and execution were verified on Linux only. Platform-specific Windows/macOS adapter builds and packaging are pending. Review regression checks cover CLI descendant cleanup, SVG style preservation and BMP180 environmental inputs after reset.

The reference bench retains 14 baseline checks and adds 9 freshly executed native sensor checks when the PICSimLab module is available (23 passed in this environment). When unavailable, the report explicitly lists the skipped native checks.

## Community catalogue expansion (2026-10-23)

278 additional offline artwork/metadata records from Adafruit, SparkFun and
Seeed Studio are available through Open-source lab. Source filtering, connector
inspection, pinned attribution and visual parts-list export are implemented.
See [component library](component-library.md). All new records are visual-only;
this expansion does not add executable boards or sensor behavior, and is not
an accuracy or superiority benchmark against Wokwi/Tinkercad.
