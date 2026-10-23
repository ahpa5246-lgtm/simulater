# Component library expansion

Goal: import at least 200 distinct named component records with offline artwork from multiple upstream repositories, not fabricate simulation support.

Architecture: deterministic build script reads pinned Adafruit, SparkFun and Seeed checkouts. Reuse the bounded SVG sanitizer, retain upstream names, connector metadata, commit/path provenance and licensing. Ship a static catalogue and adapted SVGs. Extend the existing Open-source lab with source/category filters, pagination, metadata details and a visual project parts list with JSON export. Existing Wokwi adapters remain intact.

Constraints: no new claimed simulation targets; no remote image dependencies; preserve original repository license/README attribution and per-part licenses; skip unsupported/unsafe artwork; deduplicate title and artwork; do not count tool cards as added components.

Implementation:
- [x] Add failing catalogue integrity tests: minimum 200, three source repositories, unique IDs/titles/artwork, local sanitized SVG, connectors/provenance/licenses.
- [x] Build offline catalogue using pinned source checkouts, record rejection report.
- [x] Add searchable, paginated component browser and visual parts list, persist selection and export full provenance.
- [x] Run catalogue and existing Python tests; browser exercise filters, pagination, details, selection persistence/export and all asset loads.
- [x] Review counts and limitations; verify exact uploaded Git blob hashes before updating GitHub main.

Review focus: duplicated product names; missing licenses; unsafe SVG content; excessive DOM/image load; misleading simulation status; stale selected items; empty filters; unavailable catalogue.
