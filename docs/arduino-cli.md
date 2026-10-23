# Optional Arduino CLI adapter

`boards/arduino_cli.py` adds an optional local Library Manager interface. The simulator does not require Arduino CLI. Install a trusted CLI release from [Arduino](https://docs.arduino.cc/arduino-cli/installation/), then put `arduino-cli` on PATH or set `ARDUINO_CLI_BIN` to its executable path. This is administrator configuration, never a request parameter.

## Python interface

| Function | Operation |
| --- | --- |
| `status()` | CLI version and executable availability |
| `list_cores()` | Installed cores in isolated CLI state |
| `list_libraries()` | Installed Library Manager libraries in isolated CLI state |
| `search_libraries(query)` | Search Arduino's library index with a plain query |
| `install_library(name, version)` | Install one exact registry name/version, without dependencies or overwriting |
| `compile_sketch(source, board='arduino-uno')` | Delegate to the existing compiler service with its input policy |

Manager operations return `available`, `ok`, parsed CLI `data` (or raw `output`), and `stderr`. `diagnostic` explains failures or warnings; `warnings` is also surfaced when CLI reports it in JSON. A zero exit status with initialization errors is not considered ready. Invalid names, versions, searches and unsupported boards raise `ValueError` before execution. Installation is an explicit mutation: an API/UI must invoke it only after the user selects an exact name and version. Dependencies require separate explicit selections.

No upload, serial-port access, CLI daemon, arbitrary command, platform install, Git URL or ZIP CLI installation endpoint is provided. Core listing does not mean a core can be simulated. Installing a library does not add its sensors or protocols to the simulator.

## State and compilation boundaries

State defaults to `.state/arduino-cli`; `MINA_ARDUINO_CLI_STATE` can select a different private administrator-owned directory. The optional Python `state_root` keyword exists for administration/tests; never expose it in a request body. Data, downloads and the sketchbook are separate from a normal Arduino installation. Each operation uses a private temporary working directory and explicit configuration file, then removes them. Environment overrides and credentials are not inherited; proxy settings are retained. The adapter uses argument arrays with `shell=False`, operation timeouts (30 seconds, or 90 for install), and output capped at 1 MB per stream. On POSIX it creates and kills an isolated process group; all reader waits share the operation deadline plus at most 0.2 seconds of cleanup. Windows falls back to terminating the parent and bounded daemon-reader waits, returning an explicit diagnostic if inherited pipes remain open; process-tree termination on Windows is not guaranteed. These are local process controls, not an OS sandbox or download disk quota.

Library operations may access Arduino servers and need usable indexes and network connectivity. A fresh state can report missing indexes/core-discovery components; diagnostics are returned. An administrator can prepare the isolated installation using the normal Arduino CLI with all three `ARDUINO_DIRECTORIES_DATA`, `ARDUINO_DIRECTORIES_DOWNLOADS` and `ARDUINO_DIRECTORIES_USER` environment variables pointing to this state's `data`, `downloads` and `user` directories, respectively. See the [official configuration reference](https://docs.arduino.cc/arduino-cli/configuration) and [Library Manager install reference](https://docs.arduino.cc/arduino-cli/commands-reference/arduino-cli_lib_install).

Source compilation **does not invoke Arduino CLI recipes**: CLI recipes can execute hooks and do not apply `boards/compile_policy.py`. It uses `boards.service.compile_sketch`, restricted to Uno and classic Nano, with the existing trusted AVR toolchain/core and dependency/assembly checks. CLI-installed libraries remain in a separate sketchbook and are not automatically accepted by the simulator compiler. The existing source-only library installation mechanism remains the supported compiler library path. This preserves current policy rather than introducing a second unvalidated compiler path.

## Verification

Run `python -m unittest discover -s tests -p test_arduino_cli.py -v`. Seven tests cover name/version/query rejection, exact installation arguments, missing executable diagnostics, subprocess shell/config/environment boundaries and temporary cleanup, output/timeout bounds including forked descendants retaining pipes after parent exit, and delegation to the existing compiler policy.

An additional real-executable smoke check used the official Arduino CLI 1.5.1 Linux x64 release: version succeeded; core/library listing returned JSON and initialization warnings; search and exact `Servo@1.2.2` installation returned diagnostics because this execution environment denied the CLI's DNS/network connection. Successful registry search, installation, dependency support and Arduino CLI compilation have **not** been integration verified. The adapter does not claim they were. Fixture subprocess tests are not Arduino integration tests.
