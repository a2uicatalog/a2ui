# Renderer matrix

What draws an atom (`x-renderers`), separate from where it appears (`x-surfaces`). Measured by a private harness, only CHECKED here.

## Pipeline

1. Private side (hand-run, never in CI): `python3 scripts/export_renderer_results.py` reads the gate output on the harness machine and writes `data/renderer-results/<renderer>.json` plus `manifest.json`. Only stable atoms (stage: stable or no stage in `atoms/schema.yaml`) are exported; evidence is enumerated codes and numbers; no paths, hosts or unpushed SHAs.
2. Public, committed: `python3 scripts/gen_renderer_matrix.py` writes `public/catalogue/renderer-matrix-v1.json` (served at `/catalogue/renderer-matrix-v1.json`). It is not run in CI: the committed file is checked.
   Built in CI by the normal generators (all read the committed matrix, none writes it): `generate_atom_pages.py` adds the Renderers block to every public atom page (`public/atoms/<atom>/index.html` and its `.md` twin) and writes `public/renderers/` (hub, one page per renderer, `.md` twins, logos copied from `atoms/renderer-logos/`); `gen_public_catalog.py` adds `x-renderers` per atom to `public/spec.json`, `public/catalogue/a2ui-atoms-v1.json` and `a2ui-bricks-v1.json`; `gen_compat_matrix.py` (local, README) writes a renderer summary block next to the surface block. The page fragments live in `scripts/renderer_site.py` (shared with the approved design pages `docs/renderer-draft/`, `gen_renderer_draft_pages.py`).
3. `python3 scripts/check_renderer_matrix.py` (seconds, offline; runs in `deploy.yml` after the generators): COMPLETE, FRESH (by hash; for web renderers the matrix's bundle sha256 must equal the sha256 of `public/surfaces/mcp-apps/renderer-bundle.html` in the checkout, else it fails with a re-measure message; age only warns), EVIDENCED, CONSISTENT (regenerate the matrix and compare byte for byte; the built catalogue documents carry exactly the matrix's `x-renderers`; the built pages contain the fragments `renderer_site.py` produces), PRIVATE-SAFE. Tests: `tests/test_renderer_matrix_check.py`.

Sources of the current data (all read by the private exporter only): web renderers at the shipped commit (React, Lit, Angular, a2ui-vue from the per-renderer run directories; `--web-root`/`--web-run` pick the run), CopilotKit 1.87.0 on A2UI 1.0 (its own raw gate outputs; the 1.85.0 numbers stay as a note in the registry), Flutter (lane results and parity sweep of a private build, `measured_on: private-build`, no SHA), Compose (a2ui-kmp, Compose Desktop on the JVM, v0.9.1 only).

Swapping the web data for another run (for example a deterministic-mode full pass) is a new export only: `python3 scripts/export_renderer_results.py --web-root <run root> --web-run <run dir> --measured-on shipped --commit <public sha>`, then generator, page generator, check; commit. The exporter refuses a run measured on another commit or a dirty tree, a changed package version, or an incomplete run.

## Raw results schema (`a2ui-renderer-results/1`)

Header: `renderer`, `kind` (web|flutter|compose), `renderer_version`, `dialect`, `reference_renderer`, `measured_date`, `run_id`, `measured_on` (`shipped` | `preview-unmerged` | `private-build` | `release-package` | `unrecorded`), `commit` (public SHA for `shipped`, otherwise null), `core_sha256`, `css_sha256`, `renderer_bundle_sha256`, `case_sha256` (null until the case generator exists), `wall_seconds`. Then `atoms`: one entry per stable atom, `{"cases": {<case id>: {"dialect", "checks"}}}`, or `{"cases": {}, "no_case": "no_example"}`.

Web `checks`: `painted {result pass|fail, error_code}`; `text_visible {loose, strict, strict_text, allowance}`; `pixel.<light480|dark480|light360|dark360> {result pass|fail|blank_both|reference|not_a_lane, allowance, frac, hdiff, one_blank, low, low_ref}` (low/low_ref = low-contrast counts); `overflow_360 {light360, dark360}`; `behaviour` (SAME, INERT, DIFFERENT, `n/a (no probe)`, or `not_run` when the lane was not run: shown as such, never a pass); `stability`.
Flutter `checks`: `painted {result painted|basic_lowered|unsupported|unsupported_other|invalid_payload, own_type_present, text_chars, error_codes}`; `parity_text {web_words, flutter_words, missing_in_flutter, extra_in_flutter}`.
`manifest.json` records per renderer the sha256 of its raw file, run id, build label and hashes; editing a raw file without re-exporting fails FRESH.

## Status rules (registry `rules.version` 4)

Web, per case, worst case wins (rules v4: in deterministic mode there is no allowance list; pixel and text parity are plain pass/fail and stability is proven, so nothing is `unstable`; `unstable` and its `not_verified` survive only for non-deterministic measurements, today CopilotKit 1.87.0): painted failed -> `not_supported`; pixel fail (outside the allowance if one applies), text differs from React, overflow at 360, contrast worse than React, behaviour differs -> `drawn_with_differences`; no visible text, blank on both sides, or any `unstable` check -> `not_verified`; else `drawn`; no example -> `not_measured`. Allowance-listed checks record `unstable`, never `pass`. React is the reference (pixel recorded as `reference`). INERT behaviour and absent probes do not block `drawn`.
Flutter: painted with own type -> `native`; basic_lowered -> `degraded`; unsupported* -> `not_supported`; invalid_payload -> `not_measured (invalid example)`. Worst order: not_supported, not_measured, degraded, native.
Compose: the atom's own type is a Basic component and it rendered -> `native`; rejected as unknown -> `not_supported`; no example -> `not_measured`. Compose has no implementation of our atoms; its page also shows the Basic-lane facts and the Basic behaviour summary from the header `facts`. A renderer with `measured: false` in the registry is skipped by COMPLETE.

## Determinism (det mode, the web gate mode)

At a glance: the slicer image runs Chromium with a virtual clock (rAF, timers, `performance.now` stepped in fixed frames), `Date` frozen at a fixed instant, `Math.random` seeded, SVG time fixed, an IntersectionObserver stub, fixed raster flags (no GPU raster, one raster thread, no LCD text) and a stable-shot capture (two consecutive identical screenshots). Every atom is shot twice (A, B) per renderer and environment. Stability is A == B under the pixel rule, which replaces the old allowance lists: pixel parity vs React is plain pass/fail, and the page-report text hash is compared A with B and with React.

Guarantees (measured on the shipped build, 670 atoms x 4 environments x 5 renderers): 15 of 20 cells byte-identical; the other 5 (dark 480) differ in one atom by 1 to 15 pixels of dither (channel-sum delta at most 2 of 765) and pass the rule; text hash A == B everywhere.

Does not guarantee: it holds only for a FIXED id order and 12-case chunking on the same cases file (the seeded random sequence is page-global; chunk 1 against chunk 12 differs for 10 of 33 test atoms), on the slicer image that took the baselines (any change to the shoot script, Chromium flags or case order means re-baselining) and on the cloud environment (local docker differs on two atoms). The old local custom runner is NOT deterministic, so painting, visible text and behaviour still come from the single run on the shipped commit (provenance code `f111`; pixel, overflow, contrast, text parity and stability carry `det-ab`). Two atoms, `gmail_unread_count` and `match_exercise`, consume the seeded random draws differently per renderer: their pixel and text parity vs React are excluded and they carry the note code `seeded_random_order_differs`, never a failure. Open item: reseed per case in the slicer. CopilotKit 1.87.0 has its own det pass (4 environments, A == B, one dither-only exception); its painting and visible text carry provenance `ck187` (one earlier non-deterministic run) and its behaviour is `not_run`. Atoms that fail for a cause not isolated (CopilotKit's `page_header`, `code_snippet_pair`, `image_with_caption`: content 1 px lower than React) stay differences and carry a note code.

Export: `python3 scripts/export_renderer_results.py --det-dir <dir with det_gate_raw.json and det_baselines_sha256.json> --ck187-det-dir <dir with det_gate_raw_ck187.json>` (defaults on this machine); an empty value exports the non-deterministic data alone (CopilotKit 1.87.0 then keeps the allowance logic).

## `x-renderers` in the catalogue (for the MCP side)

Next to `x-surfaces`, each component of `/catalogue/a2ui-atoms-v1.json` (and of `a2ui-bricks-v1.json`) and each atom of `/spec.json` carries `x-renderers`: an object keyed by renderer id (`react`, `lit`, `angular`, `copilotkit`, `a2ui-vue`, `flutter`, `compose`), each value `{status, reasons, measured, measured_on, renderer_version}`:

- `status`: web renderers `drawn | drawn_with_differences | not_verified | not_supported | not_measured`; Flutter `native | degraded | not_supported | not_measured`; Compose `native | not_supported | not_measured`. Only `drawn` and `native` mean "draws it as the atom intends"; `degraded` is Basic-component lowering and should not count as supported unless an agent asks (`include_degraded`).
- `reasons`: enumerated codes (`pixel_fail_dark360`, `overflow_360`, `no_visible_text`, ...), no free text. `measured`: ISO date or null (renderer not measured). `measured_on`: `shipped | preview-unmerged | private-build | release-package | unrecorded | null`. `renderer_version`: package and version string or null.
- Atoms the matrix does not cover (preview, private) carry no key. `atoms/index.json` (the compact index) is unchanged.

MCP `find_atoms` / `get_atom_schema` read the catalogue, so they can filter and report on `x-renderers` once the private worker syncs the new catalogue; that sync is a separate private step (this repo does not touch the worker).

## Still open from the design

Public case generator and `cases/manifest.json` (22 stable atoms have no example, so show `not_measured`; `case_sha256` is null); per-request slicers (cases, core, CSS); Flutter `ATOMS` filter and subset aggregator; weekly job and per-cell waivers with CODEOWNERS; CONSISTENT against the core built from the commit (core hash is recorded, not yet rebuilt in CI); behaviour lane for CopilotKit 1.87.0; Compose v1.0 and dark/360.
