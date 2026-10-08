# Wire-driven state and motion: what exists, what is missing

Written 2026-10-08 while building the preview `menu` atom. It answers one question that
`menu` actions, a `motion_transition` and presence all depend on: when a wired state
changes, how does an existing atom render differently, and what would it take to animate that?

Everything below was read from the code, not assumed. File and line references are to
`apps-script-surface/gas-wired-renderer/A2UIState.html` unless stated. The MCP Apps bundle
and the Android WebView bridge run the same engine (the bundle is byte-identical, checked by
`ops.py run android-build`), so what holds here holds on those surfaces.

## 1. How a state change reaches an atom

1. A node (ValueStore, ArrayFilter, StepNavigator ...) changes through `_set`.
2. `compileWires` (line 321) registered a listener for every non-output wire on a layout element.
   The listener calls `domBridge.setProp(layoutEl.id, propName, val)`.
3. `setProp` (line 1053) finds `#a2ui-<id>` and switches on the property name.

The properties `setProp` understands today include `visible`, `text`, `value`, `disabled`,
`checked`, `rows`, `elapsed_fmt`, `sla_state`, `pct`, `flights`, `match_rows`, and a few atom
specific ones.

A payload attaches this with `{"atom": ..., "id": "x", "props": {...}, "wire": {"visible": "#node.value"}}`.
The reverse direction (a user event writing state) is the closed `OUTPUT_WIRE_PROPS` set in
`spec/a2ui-state-v1.md` section 2.2.1.

## 2. `visible` is already generic

`setProp(id, 'visible', val)` is `el.style.display = val ? '' : 'none'` on the atom's wrapper.
It works on any atom that has an `id`, with no per-atom code. So "show this when that is true"
exists today, for every atom, including `menu`.

An earlier note in this thread said nothing wire-driven shows or hides content. That was wrong.

## 3. Enter motion already comes with it

An element that goes `display:none` to displayed restarts its CSS animation from time 0.
Checked in Chromium on 2026-10-08: `getAnimations()` went 1, 0 (hidden), 1 with
`currentTime = 0` (shown again). So any atom whose markup carries an entrance animation
(`motion_group`, the `menu` panel) replays it when a `visible` wire turns true. Nothing new is
needed for "loading -> loaded", "closed -> open" (when the open state is a wired boolean) or
"empty -> populated".

## 4. What is missing

| Gap | Why it is a gap |
|---|---|
| Exit motion | Built 2026-10-08 (see point 2 below). It was: `visible=false` set `display:none` at once. |
| Crossfade between two blocks | Two atoms with complementary `visible` wires swap instantly. The incoming one animates in; the outgoing one just disappears. |
| A wired `menu` open state | `menu` is CSS-only `<details>`. It has no output wire, so a state node cannot know it opened. |
| `menu` action items | v1 has links only. The agreed route is `onRowClick` emitting the item object (see below). |
| A global motion setting | Solved in preview: `palette` writes `--a2ui-motion-*-scale`. Only `menu` reads them. |

## 5. Recommendation

1. **Do not add `motion_transition` or `motion_presence` as atoms.** Enter is covered by section 3.
   Exit is an engine behaviour, not an atom.
2. **Exit is built (2026-10-08) as an engine behaviour.** A wired layout element takes
   `exit: "fade"` or `{effect, ease, duration, delay}`, the same shape and the same nine effects
   as the generic `enter` (`_MO_FX`), run backwards. `atoms_wired_render.gs` writes `data-mo-exit`
   plus `--mo-exit-dur/-ease/-delay` on the element wrapper; `_a2uiSetVisible` in `A2UIState.html`
   (called by `setProp` for the `visible` wire) adds `.mo-leave`, then sets `display:none` on
   `animationend` (with a timer backstop). Values are clamped and tokenised (duration token or
   0-8000 ms, ease token or four numbers, delay 0-20000 ms), the duration scales with
   `--a2ui-motion-duration-scale`, reduced motion hides at once, and showing again cancels a leave
   in progress. No `exit` means the old instant hide, so nothing existing changes.
   Example: `{"atom": "stat_card", "id": "panel", "wire": {"visible": "#open.value"},
   "exit": {"effect": "drop", "duration": "quick", "ease": "accelerate"}}`.
   Tests: `tests/test_wired_exit.py` (renderer output, clamping, hostile values, and the real
   engine function in Chromium). Not yet in `spec/a2ui-state-v1.md`: editing the spec triggers the
   prompt-update process, so that is a separate step.
3. **`menu` actions use `onRowClick`.** An action item gets `data-row-json` and the same click
   binding `data_table` and `photo_grid` use (`_a2uiBindRowClicks`), so the wire receives the item
   object. This needs a small script for wired menus only. A plain menu stays CSS-only.
4. **A wired open state is optional.** It would be a second output wire (`onToggle` already exists
   and emits a boolean), bound to the `<details>` toggle event. Add it only when a real use case
   needs state to react to a menu opening.

## 6. Still unverified

- That a `visible` wire on a bridged atom behaves the same inside the Android WebView. It should,
  since it is the same engine, but nothing has run it there.
- Whether `a2ui_wired_surface` payloads survive `A2uiAtomicCatalog.adapt()` on Android intact.
- Whether `display` toggling restarts animations identically in the GAS HtmlService iframe.

## 7. Decisions for Curtis

- Decided: exit motion goes ahead, with granular per-element control.
- Should `menu` actions (point 3) wait for a concrete wired use case, or be built next?

## 8. Global motion control (built 2026-10-08)

One `palette` block sets the feel of every motion on a surface; each element can still override.

| Control | Where | Effect |
|---|---|---|
| `duration_scale` 0.25-3 | `palette` | Multiplies every duration (`enter`, `motion_group`, wired `exit`, the `menu` panel). 2 = twice as slow. |
| `stagger_scale` 0-3 | `palette` | Multiplies the gap between staggered items (`motion_group`'s `stagger`). 0 = everything together. |
| `intensity_scale` 0-2 | `palette` | Multiplies travel distance, scale change and blur radius. 0 = fade only, no movement. |
| `intensity` 0-2 | `enter`, `exit`, `motion_group` | The element's own amount. Multiplies with `intensity_scale`. |
| `duration`, `ease`, `delay`, `effect` | `enter`, `exit`, `motion_group` | Per element, as before (tokens or clamped numbers). |

How it is wired: every effect keyframe reads `var(--mo-k,1)`, and each animated element sets
`--mo-k` to `intensity_scale x its own intensity` right beside its `animation`; durations are
`calc(Nms * var(--a2ui-motion-duration-scale,1))`; a delay is
`calc(delay + stagger * var(--a2ui-motion-stagger-scale,1))`. With no `palette` every variable falls
back to 1, so a surface without one plays exactly what it did before (the markup changed, the
computed values did not).

Verified in Chromium (`tests/test_motion_scales.py`): `duration_scale: 2` turned 0.4 s into 0.8 s;
`stagger_scale: 0.5` turned delays 0.1/0.3/0.5 s into 0.1/0.2/0.3 s; `intensity_scale: 0.5` turned a
24 px rise into 12 px; an element `intensity` of 1.5 under a 0.5 page scale gave 18 px.

Not covered, by design: film-clock atoms (`motion_timeline` and its children) own their own clock
and ignore these. `fade` and `wipe` have no distance, so `intensity` does not change them.
`intensity`, `stagger_scale` and the other palette fields are documented here and under `menu`'s
notes, not in the public `palette` or `motion_group` field lists (the preview boundary).
