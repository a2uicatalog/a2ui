# Renderer matrix (draft, local only)

What draws an atom (`x-renderers`), separate from where it appears (`x-surfaces`). Measured by a private harness, only CHECKED here.

## Pipeline

1. Private side (hand-run, never in CI): `python3 scripts/export_renderer_results.py` reads the gate output on the harness machine and writes `data/renderer-results/<renderer>.json` plus `manifest.json`. Only stable atoms (stage: stable or no stage in `atoms/schema.yaml`) are exported; evidence is enumerated codes and numbers; no paths, hosts or unpushed SHAs.
2. Public: `python3 scripts/gen_renderer_matrix.py` writes `public/catalogue/renderer-matrix-v1.json` and `a2ui-atoms-v1.renderers-draft.json`; `python3 scripts/gen_renderer_draft_pages.py` writes `docs/renderer-draft/`.
3. `python3 scripts/check_renderer_matrix.py` (seconds, offline): COMPLETE, FRESH (by hash; for web renderers the matrix's bundle sha256 must equal the sha256 of `public/surfaces/mcp-apps/renderer-bundle.html` in the checkout, else it fails with a re-measure message; age only warns), EVIDENCED, CONSISTENT (regenerate and compare byte for byte), PRIVATE-SAFE. Tests: `tests/test_renderer_matrix_check.py`.

Sources of the current data (all read by the private exporter only): web renderers at the shipped commit (React, Lit, Angular, a2ui-vue from the per-renderer run directories; `--web-root`/`--web-run` pick the run), CopilotKit 1.87.0 on A2UI 1.0 (its own raw gate outputs; the 1.85.0 numbers stay as a note in the registry), Flutter (lane results and parity sweep of a private build, `measured_on: private-build`, no SHA), Compose (a2ui-kmp, Compose Desktop on the JVM, v0.9.1 only).

Swapping the web data for another run (for example a deterministic-mode full pass) is a new export only: `python3 scripts/export_renderer_results.py --web-root <run root> --web-run <run dir> --measured-on shipped --commit <public sha>`, then generator, page generator, check; commit. The exporter refuses a run measured on another commit or a dirty tree, a changed package version, or an incomplete run.

## Raw results schema (`a2ui-renderer-results/1`)

Header: `renderer`, `kind` (web|flutter|compose), `renderer_version`, `dialect`, `reference_renderer`, `measured_date`, `run_id`, `measured_on` (`shipped` | `preview-unmerged` | `private-build` | `release-package` | `unrecorded`), `commit` (public SHA for `shipped`, otherwise null), `core_sha256`, `css_sha256`, `renderer_bundle_sha256`, `case_sha256` (null until the case generator exists), `wall_seconds`. Then `atoms`: one entry per stable atom, `{"cases": {<case id>: {"dialect", "checks"}}}`, or `{"cases": {}, "no_case": "no_example"}`.

Web `checks`: `painted {result pass|fail, error_code}`; `text_visible {loose, strict, strict_text, allowance}`; `pixel.<light480|dark480|light360|dark360> {result pass|fail|blank_both|reference|not_a_lane, allowance, frac, hdiff, one_blank, low, low_ref}` (low/low_ref = low-contrast counts); `overflow_360 {light360, dark360}`; `behaviour` (SAME, INERT, DIFFERENT, `n/a (no probe)`, or `not_run` when the lane was not run: shown as such, never a pass); `stability`.
Flutter `checks`: `painted {result painted|basic_lowered|unsupported|unsupported_other|invalid_payload, own_type_present, text_chars, error_codes}`; `parity_text {web_words, flutter_words, missing_in_flutter, extra_in_flutter}`.
`manifest.json` records per renderer the sha256 of its raw file, run id, build label and hashes; editing a raw file without re-exporting fails FRESH.

## Status rules (registry `rules.version` 3)

Web, per case, worst case wins: painted failed -> `not_supported`; pixel fail outside the allowance, overflow at 360, contrast worse than React, behaviour differs -> `drawn_with_differences`; no visible text, blank on both sides, or any `unstable` check -> `not_verified`; else `drawn`; no example -> `not_measured`. Allowance-listed checks record `unstable`, never `pass`. React is the reference (pixel recorded as `reference`). INERT behaviour and absent probes do not block `drawn`.
Flutter: painted with own type -> `native`; basic_lowered -> `degraded`; unsupported* -> `not_supported`; invalid_payload -> `not_measured (invalid example)`. Worst order: not_supported, not_measured, degraded, native.
Compose: the atom's own type is a Basic component and it rendered -> `native`; rejected as unknown -> `not_supported`; no example -> `not_measured`. Compose has no implementation of our atoms; its page also shows the Basic-lane facts and the Basic behaviour summary from the header `facts`. A renderer with `measured: false` in the registry is skipped by COMPLETE.

## Still open from the design

Public case generator and `cases/manifest.json` (22 stable atoms have no example, so show `not_measured`; `case_sha256` is null); per-request slicers (cases, core, CSS); Flutter `ATOMS` filter and subset aggregator; weekly job and per-cell waivers with CODEOWNERS; CONSISTENT against the core built from the commit (core hash is recorded, not yet rebuilt in CI); behaviour lane for CopilotKit 1.87.0; Compose v1.0 and dark/360; wiring into `gen_public_catalog.py` and `deploy.yml` (patches in `docs/renderer-matrix-patches/`, not applied).
