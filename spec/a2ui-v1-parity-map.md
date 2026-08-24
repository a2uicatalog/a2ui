# A2UI v1.0 — source of truth, mirrors, and parity guards

A reference map, not prose to read once. Built 2026-08-24 while scoping the
fix for `renderers/a2ui_v1.py`'s vocabulary drift (see `a2uithoughts.md`'s
2026-08-24 entries for the full incident). Exists because this repo already
has the identical class of problem documented once before — `CLAUDE.md`'s
own note on `mcp:<verb>` action parity ("two hand-synced lists in two
repos... guarded by a test that only catches drift, doesn't remove the
hand-sync") — and this is the SAME shape of risk on a different pair of
files. Update this table whenever a new mirror or guard is added; a stale
copy of this map is worse than no map.

## The relationships

| Python source of truth | Deployed mirror(s) | Parity guard | Ships together via |
|---|---|---|---|
| `renderers/a2ui_v1_updates.py` (`update_components`/`update_data_model`/`delete_surface`/`apply_update`) | `apps-script-surface/gas-wired-renderer/A2uiUpdates.html` | ✅ `scripts/test_a2ui_updates_js.mjs` — evals the REAL JS out of the `.html` file (no reimplementation), asserts it matches Python reference semantics | `ops.py run renderer-release` (GAS push+deploy, MCP Apps bundle regen, Worker renderer regen — `A2uiUpdates.html` is in `gen_mcp_apps_bundle.py`'s `PARTIALS` list) |
| `renderers/a2ui_v1.py`'s ChildList TEMPLATE-variant decode semantics | `apps-script-surface/gas-wired-renderer/atoms_v1_decode.gs` | ✅ `tests/test_v1_template_decode.py` — executes the real bundle JS via Node against `spec/a2ui-v1.0-upstream` semantics | same — `atoms_v1_decode.gs` is in `gen_mcp_apps_bundle.py`'s `NON_RENDERER_GS` set, still concatenated into the bundle |
| `renderers/a2ui_v1.py`'s `emit_surface()` overall createSurface SHAPE — `STANDARD_MAP` component mappings, container inversion (columns/tabs/hub/cards/etc), deterministic IDs | `apps-script-surface/gas-wired-renderer/atoms_v1_standard.gs` + `Code.gs:_rehydrateV1Surface` | ❌ **NONE.** `tests/test_a2ui_v1.py`'s own `test_childlist_v1_course_fixture` docstring says so explicitly: "the render-side proof is manual (curl against the deployed demo renderer — no automated GAS render-output harness exists yet, confirmed absent by this session's own investigation)." Confirmed still true 2026-08-24. | same process, but nothing verifies the two sides actually agree before it ships |
| `renderers/a2ui_v1.py`'s `action_response()`/`call_function()`/`function_response()` | none found — no GAS/JS file references these specific shapes | n/a (nothing to keep in parity yet) | n/a |

## What this means for the current fix (PR 2, in progress)

The two rows with real parity tests are low-risk to change: fix the Python
side, update the `.gs`/`.html` mirror to match, run the existing test, it
tells you the truth.

The `atoms_v1_standard.gs` row is the real exposure — it's exactly the code
path `emit_surface()`'s fix touches most (removing `surfaceProperties`,
restructuring how title/theme/catalogs are carried), and there's no
automated check that the GAS side still agrees after the Python side
changes. Building a real parity test for this row — same pattern as
`test_a2ui_updates_js.mjs`: eval the actual `atoms_v1_standard.gs`/
`_rehydrateV1Surface` JS, feed it real `emit_surface()` output, assert it
decodes back to something render-equivalent — closes this repo's own
already-identified gap, not a new one invented for this fix. Worth building
as part of PR 2 itself, not deferred again.

## Where this is wired in

- `ops/project-ops.yaml`'s `renderer-release` process entry (a2ui-private)
  has a comment pointing here — the process that ships every row in this
  table already exists and needs no changes; what's missing is the guard,
  not the deploy path.
- `a2uithoughts.md` logs the investigation that produced this map, with a
  link back here for the durable reference (thoughts entries are a
  narrative log; this file is the thing to actually consult later).
