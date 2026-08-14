# Wire emission — Output Wire Contract v0.1

**Status:** Draft v0.1 (2026-08-14)
**Applies to:** every prop in `OUTPUT_WIRE_PROPS` (`A2UIState.html`).
**Gated by:** `tests/test_wire_emission.py`, both directions — the binder and
this table must agree, and a new prop in either fails the build.

## Why

A wired payload declares `wire: {onRowClick: "#sel.setValue"}` and the engine
delivers *something* into `sel`. What that something IS has never been written
down. It lives only in the binder's `bindOutput` call sites, and it is not
uniform: five different shapes across eleven props, including one prop that
emits `null` where every reader assumes it emits the query.

Consumers therefore discover the shape by being wrong in production. On
2026-08-14 `maison` assumed `onRowClick` emits an id; it emits the whole row.
Two pages broke simultaneously — a status change and a shopping-list update
both answered "no record with that id", naming the one thing that was
certainly not wrong — and 317 passing tests missed it, because every one of
them drove the verbs the way a test does rather than the way a browser does.

`test_wired_binding.py` could not have caught it either. It asks *did a
binding attach*, which is a different question from *what value flows*. Both
are needed; only the first existed.

## The table

| prop | emits | shape |
|---|---|---|
| `onChange` | the control's current value | string |
| `onClick` | nothing — the click IS the signal | `null` |
| `onToggle` | the checkbox state | boolean |
| `setDone` | the checkbox state | boolean |
| `onRowClick` | **the whole clicked row** | object |
| `onReorder` | the moved item's new position | `{id, order, group?}` |
| `onSearch` | **nothing** — see below | `null` |
| `onConfirm` | the gate's `decision_id` | string (may be empty) |
| `onCancel` | the gate's `decision_id` | string (may be empty) |
| `onFlightClick` | the clicked flight | object |
| `onAssign` | the assigned person | object |

### The three that surprise people

**`onRowClick` emits the ROW, not an id.** `_a2uiBindRowClicks` reads
`data-row-json` and hands it over intact. That is the right contract — a click
may want more than one field — but a consumer writing `collect: {id:
"#sel.value"}` gets a dict where the server expects a string, and
`str({...})` matches no record. **A wire cannot narrow it**, because
`_parseWire` splits at the first dot: `#sel.value.id` reads a literal property
named `"value.id"` and renders blank. The narrowing must happen server-side.

**`onSearch` emits `null`.** The query is NOT delivered. The search control
writes its text into a store via `onChange` like any other input, and
`onSearch` is only the *trigger*; the action reads the text through its own
`collect{}`. Wiring `onSearch` to a store expecting the query silently stores
`null`.

**`onClick` emits `null`.** Documented because `visible: "#act.isSuccess"`-style
reasoning tempts people to treat the click's value as meaningful. It is not.

## Consumer rule

An action's `collect{}` entry reading `#<store>.value`, where that store is
written by an output wire, must accept the shape this table declares for that
wire. The two failure modes:

- **object where a scalar is expected** — the `onRowClick` case. Narrow it
  server-side, at the one boundary that sees every shape a selection can
  arrive in (a clicked row, or a bare id seeded from a link).
- **`null` where a value is expected** — the `onSearch` case. Read the value
  from the store the control writes to, not from the trigger.

`maison`'s `test_every_row_click_target_survives_being_handed_a_row` is the
prototype: it walks the payload's wiring, finds stores fed by row clicks,
finds the actions collecting them, and asserts each handler narrows. It reads
the wiring rather than a list somebody maintains, so a page wired the same way
is covered the day it is written.

## Not covered by this version

Input wires (state → DOM: `text`, `value`, `visible`, `rows`, `href`,
`subject_id`, …). They have the reverse problem — what a sink ACCEPTS — and
deserve their own pass. `rows` expecting an array and `text` expecting a
scalar is the same class of undeclared assumption.
