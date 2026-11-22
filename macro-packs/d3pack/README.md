# d3pack: the d3 atoms as Python macros

d3pack is 28 Python macros that draw d3-style charts as SVG. Eighteen of them are the macro twins of atoms in this catalogue: `treemap`,
`sunburst`, `circle_pack`, `histogram`, `box_plot`, `waterfall`, `sankey_flow`, `chord_diagram` and so on (the full list is below).
You give a macro the data and a few options, and it returns the picture.

## Where it comes from

The charts are based on [d3](https://d3js.org), the visualisation library by Mike Bostock, and on its separate packages (d3-array,
d3-hierarchy, d3-chord, d3-shape, d3-contour, d3-sankey, and d3-delaunay, whose authors are Observable, Inc. and Mapbox). d3 draws in a
browser with JavaScript. d3pack re-implements the layouts in Python, so the output is not pixel-identical to d3.
A few modules are close ports of d3's own code; a few follow a d3 method with their own structure; the rest are our own.
[`../LICENCE-AUDIT.md`](../LICENCE-AUDIT.md) says which is which, file by file, and [`../THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md)
carries the d3 licences (ISC, and BSD-3-Clause for d3-sankey). Our own code is MIT ([`../LICENSE`](../LICENSE)).

## Why it is interesting

- **The picture comes from a few parameters.** An agent does not have to write chart code or SVG. It sends the data, and Python draws it:
  standard library only, no browser, no network, no model. The same input gives the same picture, and the tests check that for each macro.
- **Every chart carries its own alternative.** A macro returns the SVG together with a data table, a short text description and notes
  (for example "Only 2 usable items (the atom expects 4 to 12)."), so the chart is readable without seeing it and the limits are said out loud.
- **It works wherever an image does.** The output is plain SVG, which any renderer can show as an image, so these charts do not depend on a renderer
  that knows the catalogue's atoms. The messages the pack emits are validated against the upstream A2UI 1.0 schemas in the tests.
- **It is checked before it is returned.** Each SVG passes `verify_rich` (in `rich.py`): finite animation only, no scripts, no keyframes.
  The check fails closed and sanitises nothing.

## Use it

```python
import sys; sys.path.insert(0, "macro-packs")           # the import root
from d3pack.treemap import treemap

items = [{"path": ["Europe"], "name": "France", "value": 40},
         {"path": ["Europe"], "name": "Spain", "value": 14},
         {"path": ["Asia"], "name": "Japan", "value": 30},
         {"path": ["Asia"], "name": "India", "value": 22}]
res = treemap(items, title="Orders by country")["squarified"]
open("treemap.svg", "w").write(res["svg"])
print(res["alt"])      # Treemap: Orders by country. Total 106 in 4 items and 2 top-level groups; ...
print(res["table"])    # Europe/France 40 (37.7%); Europe/Spain 14 (13.2%); ...
```

A macro returns a dictionary with one entry per layout, and each entry holds `svg`, `alt`, `table`, `notes` and the layout's own geometry.
`make_payloads.py` builds a demo input for every macro (synthetic data, no model); it is also the quickest way to see each macro's arguments.

## The macros that are catalogue atoms

`arc_diagram`, `box_plot`, `chord_diagram`, `circle_pack`, `contour_plot`, `decision_tree`, `gauge_sla`, `heatmap_calendar`, `histogram`,
`sankey_flow`, `spring_nodes`, `stacked_area`, `sunburst`, `swimlane`, `treemap`, `venn_diagram`, `voronoi`, `waterfall`.

The other ten (`availability`, `bar_chart`, `beeswarm`, `brick_build`, `connect_four`, `latency_ledger`, `line_chart`, `ridgeline`,
`svg_lab`, `venn`) have no atom of the same name. The catalogue's `org_chart` has no macro of its own: `decision_tree` draws trees.

## Tests

From the repository root. These need only the standard library:

    for t in atom_convert availability bricks gauge glass_monitor kpi_strip perf rich; do python3 -B macro-packs/tests/test_$t.py; done

These validate every emitted message against the upstream A2UI schemas, so they need `pip install jsonschema` and a checkout of the upstream
A2UI repository. Without one they print `SKIPPED` and exit:

    A2UI_UPSTREAM=/path/to/upstream python3 -B macro-packs/tests/test_pack.py     # also: stats, fields, flow, networks, hierarchy

`test_perf` compares the pack's output byte for byte with hashes taken before its speed fixes, so a change that alters a drawing is caught.

## What is not here

- The tests that need a browser or node (guard, html, gauge_modern, motion, shatter, stat_card, latency, svg_repair, and the fuzzers) stay in the
  private repository. The modules they cover, `html_static`, `gauge_modern`, `motion`, `shatter`, `stat_card`, `latency_ledger` and `svg_repair`, are published
  without them.
- Timings on a Cloudflare Python Worker have not been measured for this pack, so none are claimed here.
- `conformance/`, which compares reference numbers against the real d3 packages, and saved model-run outputs stay private.

Independent, unofficial catalog, not affiliated with, endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's. MIT License.
