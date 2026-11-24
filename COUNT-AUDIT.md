# Count and version audit, 2026-11-15

Published count N = len(components) of public/catalogue/a2ui-atoms-v1.json = 573 (spec.json and atoms/index.json agree).
Classes: TOTAL (must equal N, exact), PER-SURFACE/PER-RENDERER (computed, shown "X of N"), DATED (carries its date), NOT-CATALOGUE.
Scan: all tracked public/**, content/, README, SKILL files, mcp/, sdk/, skills/, docs/, prompts/, scripts/ for `\d{3}\+? atoms|components`, hyphen forms, "N+", "over/about N", "~N". Blog posts and public/gallery are dated records and are skipped.

## Public outputs

| Path | Quote | Class | Action |
|---|---|---|---|
| public/index.html | "550+ typed atoms", "550+" hero stat, "Search and preview 550+ atoms", meta/og/twitter/JSON-LD "550+", "550+ atoms" counter | TOTAL (approximation) | generate_atom_pages.py now prints the exact count (it was rounded down to 50 on purpose); held by CLAIMS in gen_atom_count.py |
| public/index.html | "563 of 550+ atoms rendering live" | PER-SURFACE | now "563 of 573" |
| public/index.html (landing film) | stat_card "Typed atoms" value "500+" and its code lines | TOTAL (approximation) | film is built in the private repo with a typed 500+; render_landing_film() substitutes N at render time; builder fix still needed (see report) |
| public/what-is-a2ui.md and /what-is-a2ui/index.html | "545 published components" (stale twin), film pill "500+ components", film letter "version": "v1.0" | TOTAL, version | film JSON rebuilt (N read from the catalogue, "1.0"); pillar page and twin regenerated; CI now builds twins after the pillar pages |
| public/llms.txt | "474 typed atoms" (blog 004 blurb) and "573 atoms" | TOTAL | blurb no longer carries a number; the other is generated from N |
| public/openapi.json, openapi.yaml | "Serves the 474 published atoms" | TOTAL | f-string from n_atoms in gen_openapi.py |
| public/renderer/index.html, renderer.md | "550 atoms, ready to go" (Apps Script count) | PER-SURFACE | "550 of 573 atoms" (gen_renderer_page.py) |
| public/renderers/*/index.html | "Drawn: 517 atoms", "Text parity ... checked on 279 atoms" | PER-RENDERER | all "X of 573 atoms" (gen_renderer_draft_pages.py); docs/renderer-draft regenerated |
| public/surfaces/*/index.html | "507 atoms available on this surface", title "507 components" | PER-SURFACE | "507 of 573" in title, description and lead |
| public/surfaces/*, atoms/timeline, atoms/stages.json | sample timeline event "467 atoms" | stale committed copy of a generated sample (generator already uses N) | refreshed to 573 |
| public/surfaces/mcp-apps/renderer-bundle.html | "290+ atoms" in a demo feature card | TOTAL (approximation) | NOT fixed: editing the bundle changes its hash and fails the renderer-matrix FRESH check; allowlisted with a reason; needs a bundle rebuild and re-measure |
| public/about, developers, docs, atoms hub, try, ard.json, ai-catalog.json, catalogue json, custom-catalog guide pages, MCP server card | "573 ..." | TOTAL, already N | now covered by the sweep test |
| public/renderers/compose* | "about 500 registered custom components" | NOT-CATALOGUE (Compose-side registry, approximate by design; no atom total) | left; not matched by the test |
| public/spec.json, ard.json, catalogue json | "Browse 2500+ icon names" | NOT-CATALOGUE (Google Fonts icons) | left |

## Sources

| Path | Quote | Class | Action |
|---|---|---|---|
| README.md, SKILL.md, mcp/*, plugin.json, sdk/python/pyproject.toml, docs/quickstart-claude.md, skills/*/SKILL.md | "573 atoms" etc. | TOTAL | already in CLAIMS; unchanged |
| prompts/a2ui-builder-gem*.md | "all 573 atoms" | TOTAL | added to SWEEP_GLOBS |
| payloads/learn-a2ui-modules/*.json | `"version": "v1.0"` in spec quotes | version | now "1.0" |
| tests/test_basic_catalog_coverage.py:361 | `{"version": "v1.0", ...}` | fixture of OUR renderer input; the GAS decoder accepts both | changed to "1.0" (our emitter's form) |
| scripts/check_registry_listings.py | forbade exact counts in the Smithery listing | EXTERNAL hand-typed listing | RETIRED 2026-11-24 (owner: "retire the smithery"): the listing is no longer maintained and is stale (shows 15 tools, the server serves 40); the owner removes it in the Smithery dashboard; the check failed weekly; script, test and workflow removed |
| scripts/build_web_preview.py, catalogue_stage_deck.py | "220 atoms", "100 atoms" | NOT-CATALOGUE (sample deck copy) | left |
| atoms/atom-packs.yaml "499", atoms/schema.yaml "468 typed atoms", gen_atom_embeddings.py "468", gen_pack_map.py "497", check_eval_coverage.py "468", renderers/googlechat.py "498", docs/accessibility.md "650 atoms audited", docs/renderer-matrix.md "670 atoms x 4 environments", docs/proposals "~550", spec/roadmap-md-v0.1.md "467", articles/* | historical comments or measurements, not public site output | DATED or internal | left; not public |
| blog posts, public/gallery | various | DATED records | skipped by design |
