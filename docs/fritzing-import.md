# Fritzing visual parts

The visual parts importer accepts one `.fzpz` ZIP as artwork. Imported parts have
`support: "visual-only"`: connector names are labels, and imported SPICE/model
sections do not create simulation models, board firmware targets, or electrical
behavior. Use the simulator's explicitly supported devices for simulation.

`boards.fritzing_parts.import_part(data, root=None)` returns an ID, title (`name`),
author, license, properties, connector names, preserved attribution files, support
status, and `svgUrl`. `list_parts(root=None)` loads persisted metadata;
`svg_path(id, root=None)` locates sanitized artwork. The default storage directory
is `.state/visual-parts`; a supplied root is the visual-parts directory itself.
Each import uses a fresh random 32-character lowercase hexadecimal ID and saves
`metadata.json` and `part.svg` beneath that ID. The SVG URL is
`/api/visual-parts/<id>.svg`.

## Supported subset and limits

A ZIP must be at most 1,000,000 bytes, contain at most 32 entries and at most
3,000,000 declared uncompressed bytes, and contain exactly one `.fzp` XML file.
Traversal, absolute/Windows paths, duplicate file names, and symbolic links are
rejected. Files are read inside the ZIP; archive paths are never extracted.

The FZP must name one `views/breadboardView/layers.image`. Its artwork must match
exactly one ZIP entry using a slash path (optionally beneath a bundle directory)
or the usual flattened `svg.breadboard.filename.svg` export convention. A missing
or ambiguous image fails import. This is a tested import subset, not a claim of
complete Fritzing file compatibility.

Both XML documents reject DTD and ENTITY declarations, with one SVG-only
exception: the exact inert W3C SVG 1.1 PUBLIC declaration used in the official
fixture is removed before XML parsing. Its public ID must be
`-//W3C//DTD SVG 1.1//EN` and its system ID must be
`http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd`, using the fixture's exact
double-quoted declaration. Internal subsets, entity declarations, alternate URLs,
and other declarations remain forbidden. The importer never parses or fetches a
DTD.

SVG is rebuilt using a static element and attribute allowlist. Basic geometry,
text, colors, transforms, simple inline presentation styles, clipping, gradients,
and local gradient references survive. Scripts, event handlers, `foreignObject`,
images, `use`, animation, stylesheet elements, unknown namespaces, external
references, and unsafe CSS are removed. SVG complexity and nesting are bounded.
Unsupported artwork features can change appearance; review the visual result.
Allowed inline styles become SVG presentation attributes so they render under
the server's strict content security policy. Original inline style values take
precedence over the corresponding presentation attributes; no `style` attribute
survives sanitization.

## Attribution and reuse

Only import artwork that you are authorized to reuse. An open-source label alone
does not remove attribution or ShareAlike requirements. The importer retains FZP
author/license/properties and inert text from included LICENSE, COPYING, NOTICE,
and AUTHORS files. It does not infer a new license when an archive omits one.
Keep the source credits and license with any exported or redistributed graphics.
Sanitization modifies artwork, so identify that modification where the license
requires it. For CC BY-SA artwork, preserve credit, link the license, identify
changes, and distribute adaptations under the applicable ShareAlike license.

The integration test embeds the real official Fritzing red 3 mm LED metadata and
breadboard artwork, fetched through the GitHub connector at commit
`27535f2fd02097be9bed229b75aa8e9be282a4a0`:

- [FZP, author Stefan Hermann](https://github.com/fritzing/fritzing-parts/blob/27535f2fd02097be9bed229b75aa8e9be282a4a0/core/LED-generic-3mm.fzp)
- [Original Fritzing breadboard SVG](https://github.com/fritzing/fritzing-parts/blob/27535f2fd02097be9bed229b75aa8e9be282a4a0/svg/core/breadboard/LED-3mm-red-leg.svg)
- [Repository graphics/documentation license](https://github.com/fritzing/fritzing-parts/blob/27535f2fd02097be9bed229b75aa8e9be282a4a0/LICENSE.txt)
- [Creative Commons Attribution-ShareAlike 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/)

Credit: Fritzing graphics; LED metadata by Stefan Hermann. The fixture retains
original artwork in the test constant and imports without caller modifications.
The importer removes its exact inert SVG 1.1 DOCTYPE before parsing and sanitizes
the resulting artwork. Tests separately reject internal DTD subsets and changed
system URLs. These adapted test graphics remain CC BY-SA 3.0. Other imported
parts can have different licenses.

Run the importer tests with:

```sh
python -m unittest discover -s tests -p test_fritzing_parts.py -v
```
