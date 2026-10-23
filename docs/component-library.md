# Community component library

The Open-source lab includes **278 new distinct named visual component records**
from three additional repositories. The existing 50 Wokwi Elements remain a
separate collection. This is a larger artwork/metadata library, not 278 new
simulation models. Product variants may exist; title and sanitized artwork
hash deduplication do not establish electrical uniqueness across collections.

| Source | Imported records | Artwork license |
| --- | ---: | --- |
| adafruit/Fritzing-Library | 110 | CC BY-SA 3.0 |
| sparkfun/Fritzing_Parts | 110 | CC BY-SA 4.0 |
| Seeed-Studio/fritzing_parts | 58 | CC BY-SA 4.0 |

Use search, repository and category filters to find a component. Browse 24 cards
per page. “View connectors & source” shows the connector labels, extracted
properties, original source, attribution and license. “Add to visual parts
list” persists a reference list in this browser. JSON export includes all
provenance and explicitly identifies the list as visual-reference-only. It
cannot be loaded as a wired simulation circuit. There is no new electrical
adapter, MCU target, drag-and-wire behavior or inferred physical model.

## Rebuild

Clone the three repositories into directories named `adafruit`, `sparkfun` and
`seeed` under one source directory. Check out the exact commits recorded in
`web/vendor/components/catalog.json`, then run:

```sh
python scripts/vendor-components.py /path/to/source-directory
python -m unittest discover -s tests -p test_component_catalog.py -v
npm run test:components-browser
```

The builder does not fetch files. It reads individual `.fzpz` archives and
standalone `.fzp` files, with bounded archive expansion, then reuses the existing
SVG allowlist sanitizer. Unsupported/unsafe inputs are skipped and recorded in
`web/vendor/components/build-report.json`. At most 110 accepted parts are taken
per source in deterministic path order. No filesystem paths in ZIPs are extracted.

All shipped SVGs are adaptations under their source's indicated CC BY-SA license.
The adaptation removes active content and unsupported SVG features; it can
change appearance. The original FZP/SVG is available through each pinned source
link. Author fields are retained; repository organization is the fallback when
no author is present. Original README and license notices are distributed in
`web/vendor/components/notices/`, including Adafruit's PigHixx sub-art credits.
These artwork terms do not relicense the simulator application as a whole.

## Verification scope

Integrity checks verify the minimum count, three distinct repositories, unique
titles/IDs/artwork hashes, pinned provenance, attribution files, local SVG hash
integrity and absence of prohibited active elements. Browser checks exercise
filters, pagination, details, selection persistence/removal, exported metadata,
all 278 SVG HTTP responses, narrow-screen overflow and JavaScript errors.
These checks do not validate each drawing against a physical product or its
pinout against a manufacturer datasheet. Automated category heuristics are for
discovery only. Existing circuit and firmware tests remain separate.

Verification on 2026-10-23: 65 Python tests and 11 Node tests passed. The new
component-library browser suite passed, including all 278 artwork responses.
The existing upstream browser suite passed with `ARDUINO_CLI_BIN` configured.
Its first run without that environment variable failed its CLI-status assertion;
this was corrected by configuring the existing local executable before rerunning.
No registry installation or physical hardware comparison was performed.
