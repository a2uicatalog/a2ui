# Licence audit of d3pack/*.py (2026-11-14)

Method: each file read or searched for d3 references; PORT files compared line by line with an npm install of the d3 packages. Several OWN files (the small demos, registries, latency_ledger, brick_build, availability and similar) were checked by grep and docstring plus a skim, not read line by line. No automated similarity tool was used. Classes: PORT = close structural translation of a named d3 module; METHOD = same algorithm, own code; OWN = no d3 algorithm.

## Module versions and licences

| Module | Version | Licence | Basis |
|---|---|---|---|
| d3-array | 3.2.4 | ISC | stated in notices; also read from the installed d3-array package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-hierarchy | 3.1.2 | ISC | stated in notices; also read from the installed d3-hierarchy package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-chord | 3.0.1 | ISC | stated in notices; also read from the installed d3-chord package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-shape | 3.2.0 | ISC | stated in notices; also read from the installed d3-shape package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-contour | 4.0.2 | ISC | stated in notices; also read from the installed d3-contour package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-delaunay | 6.0.4 | ISC | stated in notices; also read from the installed d3-delaunay package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |
| d3-sankey | 0.12.3 | BSD-3-Clause | stated in notices; also read from the installed d3-sankey package.json (version, license field) and its LICENSE file (text identical to the notices block). Versions match the pinned versions in the private conformance test. |

The d3 packages were installed from npm for this audit; the installed versions match the table. No mismatch found.

## Per file

| File | Class | d3 module | Evidence |
|---|---|---|---|
| __init__.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| arc.py | OWN | - | Mentions d3 scalePoint spacing only as a formula (even steps); own code. |
| availability.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| basic_charts.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| beeswarm.py | OWN | - | Own bucketed placement, no d3-force. |
| box_plot.py | METHOD | d3-array 3.2.4 (quantileSorted) | quantile() is the R-7 formula in three lines; the formula is standard, but it was written to the same arithmetic as quantileSorted. Judged METHOD, not PORT. |
| brick_build.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| chord.py | METHOD | d3-chord 3.0.1 | undirected_layout reproduces d3.chord semantics (k, subgroup sort, source = larger direction) with own structure; directed_layout is an own approximation (docstring: "approximate"). |
| common.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| connect_four.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| contour.py | PORT | d3-array 3.2.4 (ticks.js, nice.js) | _incr/d3_ticks/d3_nice follow tickIncrement/ticks/nice; compared against installed source. Marching squares (edge-key linking, mean-test saddles) is a different construction: METHOD; KDE, drawing own. |
| decision_tree.py | OWN | - | Own tree placement (leaf rows, centred parents), not d3.tree. |
| demos_booking.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_bricks.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_fields.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_flow.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_hierarchy.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_latency.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_networks.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| demos_stats.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| heatmap_calendar.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| histogram.py | PORT | d3-array 3.2.4 (ticks.js) | _spec/d3_ticks match tickSpec/ticks statement for statement (power, error, factor, i1/i2, inc<0 branch, recursion for count<2). Bin edges, readers, drawing own. |
| html_static.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| lanes.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| latency_ledger.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| pack.py | METHOD | d3-hierarchy 3.1.2 (pack) | Own tangent-candidate placement and Badoiu-Clarkson enclosing circle; not d3 front-chain/enclose (docstring says NOT d3.pack). |
| registry_fields.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| registry_flow.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| registry_hierarchy.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| registry_networks.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| registry_stats.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| rich.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| ridgeline.py | OWN | - | Uses histogram helpers; no d3 code of its own. |
| sankey.py | METHOD | d3-sankey 0.12.3 | Own column assignment, cycle drop and ribbon stacking; docstring says not d3-sankey relaxation. Only the k-scaled node/link sizing idea is shared. |
| spring_nodes.py | OWN | (d3-force not listed) | Own deterministic spring/charge simulation with golden-angle start; no d3-force code seen in the part read (layout()). |
| stacked_area.py | PORT | d3-shape 3.2.0 (order/insideOut.js, offset/wiggle.js) | inside_out() same steps as insideOut (sums, top<bottom deal, bottoms reversed + tops); wiggle block has the same s1/s2/s3 recurrence as wiggle.js. Silhouette/expand trivial; drawing own. |
| sunburst.py | METHOD | d3-hierarchy 3.1.2 (partition) | Children split parent span by value, largest first; own tree build and recursion, no partition.js structure. |
| svg_lab.py | OWN | - | No d3 algorithm; own utility, data or drawing code (grep for d3 shows only names/CSS classes). |
| treemap.py | PORT | d3-hierarchy 3.1.2 (treemap/squarify.js) | squarify() mirrors d3 squarify: alpha, beta, minRatio/newRatio row growth, dice/slice by dx<dy; docstring says "ported". Rest of file own. |
| venn.py | OWN | - | Own bisection geometry. |
| voronoi.py | METHOD | d3-delaunay 6.0.4 | Sutherland-Hodgman half-plane clipping, O(n^2); no Delaunay/Voronoi code from d3-delaunay. |
| waterfall.py | OWN | - | nice_step is a generic 1-2-5 rounding, not d3 tick code. |

## Notes

- PORT files carry a header comment after the docstring naming the module, version, licence and copyright holder. Only the named functions are ported; the rest of each file is own code.
- UNSURE: none classed UNSURE. box_plot.py quantile is the closest call (a standard formula).
- sankey.py: the notices file says d3-sankey is used for node/link sizing; the code read shows no d3-sankey structure, so the BSD-3 text is retained as a precaution.
- Own code licence: MIT, see LICENSE.
