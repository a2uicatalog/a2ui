# Renderer matrix (draft, local only)

What draws an atom (`x-renderers`), separate from where it appears (`x-surfaces`). Measured by a private harness, only CHECKED here.

## Pipeline

1. Private side (hand-run, never in CI): `python3 scripts/export_renderer_results.py` reads the gate output on the harness machine and writes `data/renderer-results/<renderer>.json` plus `manifest.json`. Only stable atoms (stage: stable or no stage in `atoms/schema.yaml`) are exported; evidence is enumerated codes and numbers; no paths, hosts or unpushed SHAs.
2. Public: `python3 scripts/gen_renderer_matrix.py` writes `public/catalogue/renderer-matrix-v1.json` and `a2ui-atoms-v1.renderers-draft.json`; `python3 scripts/gen_renderer_draft_pages.py` writes `docs/renderer-draft/`.
3. `python3 scripts/check_renderer_matrix.py` (seconds, offline): COMPLETE, FRESH (by hash; age only warns), EVIDENCED, CONSISTENT (regenerate and compare byte for byte), PRIVATE-SAFE. Tests: `tests/test_renderer_matrix_check.py`.

After a new gate run (for example on the shipped commit): write the same schema from the new output (extend or replace the exporter's input section; use `--measured-on shipped` and fill `commit` with a public SHA), run exporter, generator, page generator, check; commit. The generator does not change.

## Raw results schema (`a2ui-renderer-results/1`)

Header: `renderer`, `kind` (web|flutter), `renderer_version`, `dialect`, `reference_renderer`, `measured_date`, `run_id`, `measured_on` (`shipped` | `preview-unmerged` | `unrecorded`), `commit` (public SHA or null), `core_sha256`, `css_sha256`, `renderer_bundle_sha256`, `case_sha256` (null until the case generator exists), `wall_seconds`. Then `atoms`: one entry per stable atom, `{"cases": {<case id>: {"dialect", "checks"}}}`, or `{"cases": {}, "no_case": "no_example"}`.

Web `checks`: `painted {result pass|fail, error_code}`; `text_visible {loose, strict, strict_text, allowance}`; `pixel.<light480|dark480|light360|dark360> {result pass|fail|blank_both|reference|not_a_lane, allowance, frac, hdiff, one_blank, low, low_ref}` (low/low_ref = low-contrast counts); `overflow_360 {light360, dark360}`; `behaviour` (SAME, INERT, DIFFERENT, or `n/a (no probe)`); `stability`.
Flutter `checks`: `painted {result painted|basic_lowered|unsupported|unsupported_other|invalid_payload, own_type_present, text_chars, error_codes}`; `parity_text {web_words, flutter_words, missing_in_flutter, extra_in_flutter}`.
`manifest.json` records per renderer the sha256 of its raw file, run id, build label and hashes; editing a raw file without re-exporting fails FRESH.

## Status rules (registry `rules.version` 2)

Web, per case, worst case wins: painted failed -> `not_supported`; pixel fail outside the allowance, overflow at 360, contrast worse than React, behaviour differs -> `drawn_with_differences`; no visible text, blank on both sides, or any `unstable` check -> `not_verified`; else `drawn`; no example -> `not_measured`. Allowance-listed checks record `unstable`, never `pass`. React is the reference (pixel recorded as `reference`). INERT behaviour and absent probes do not block `drawn`.
Flutter: painted with own type -> `native`; basic_lowered -> `degraded`; unsupported* -> `not_supported`; invalid_payload -> `not_measured (invalid example)`. Worst order: not_supported, not_measured, degraded, native.
Compose has `measured: false` in the registry and is skipped by COMPLETE.

## Still open from the design

Public case generator and `cases/manifest.json` (22 stable atoms have no example, so show `not_measured`; `case_sha256` is null); per-request slicers (cases, core, CSS); Flutter `ATOMS` filter and subset aggregator; weekly job and per-cell waivers with CODEOWNERS; CONSISTENT against the core built from the commit (needs a re-measure on the shipped build); wiring into `gen_public_catalog.py` and `deploy.yml` (patches in `docs/renderer-matrix-patches/`, not applied).
