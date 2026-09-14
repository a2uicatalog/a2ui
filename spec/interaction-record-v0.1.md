# Interaction record — v0.1

**Status:** Draft v0.1 (2026-09-14). **Requires no new engine primitive.** This
document is a convention for composing primitives that already ship in
`spec/a2ui-state.yaml` — `action_node`, `ValueStore`, `StringTemplate`,
`Computed` — not a new wire mechanism.
**Applies to:** any atom where a user makes a selection or commits an action
(`seat_map`, `slot_scheduler`, `option_plan_builder`; candidates for later
adoption: `choicebox_group`, `variant_selector`).

## Why

Chat-support generative UI elsewhere (Cresta's "Custom UI Components") treats
two things as required for any interactive component, not optional polish:

1. A named state machine — loading / empty / error / selected / confirmed —
   so a booking-shaped surface behaves consistently regardless of who authored
   it.
2. A plain-text record of what happened ("Customer selected seat 14C"), kept
   even when the visual can't render, for handoff to a human and for
   logging/audit.

Neither exists here as a documented pattern today, but the machinery for both
already shipped for other reasons. This spec names the composition so future
atoms don't reinvent it, and so it stops living only inside three new atoms'
descriptions.

## State mapping

| Cresta state | This estate's primitive |
|---|---|
| loading | `action_node.isPending` |
| error | `action_node.isError` (+ `action_node.error` for the message) |
| confirmed | `action_node.isSuccess` (+ `action_node.result` for the payload) |
| empty | a `DerivedStore`/`ArrayFilter` result of length 0 |
| selected | a local `ValueStore` the visual atom writes to |

An atom author does not add new props for these — they wire the existing
`action_node`/`ValueStore` outputs to whatever the atom already exposes for
conditional rendering. `slot_scheduler`'s confirmation block, for example, is
shown when `#book_action.isSuccess` is true; nothing atom-specific is needed
to represent "confirmed."

## Plain-text record

Every atom that opts into this convention declares a `summary_template`
field: a string with `{placeholder}` slots, e.g. `"Selected seat {label}"`.
The author wires a `StringTemplate` primitive (`spec/a2ui-state.yaml`) whose
`inputs` read the *same* store the visual atom reads or writes — not a
parallel computation — so the sentence and the picture can never disagree.

```json
{
  "id": "seat_summary",
  "primitive": "StringTemplate",
  "props": {
    "template": "Selected seat {label}",
    "inputs": { "label": "#seat_pick.value.label" }
  }
}
```

This resolved text is the thing to show on a surface where the atom itself is
`incompatible_on` (email, pdf, google-chat, per the atoms' own `surfaces`
declarations) — a host degrading the surface renders the `StringTemplate`
output as plain text instead of silently dropping the selection, and the same
text is what a handoff/audit log should capture. This mirrors, and
generalizes, the existing `freeform_canvas.summary` field (`atoms/schema.yaml`)
— "plain-text description used as the accessibility label and as the full
content on text-only surfaces" — applied to a live selection instead of a
static diagram.

## Live computed values

A value that changes as the user interacts (`option_plan_builder`'s running
total) has two valid implementations, matching the two renderer targets this
repo ships:
- The standalone `renderers/web_article.py` renderer computes it itself
  (inline script summing `price_delta`), the same relationship `live_metric`
  has to its own animation — self-contained, no wiring required.
- A full wired surface instead binds the atom's `total_expr` field to a
  `Computed` primitive (`spec/a2ui-state.yaml`) summing the relevant inputs,
  so the total participates in the payload's broader state graph. This is a
  direct consequence of the frozen client-side derivation boundary already
  declared in `spec/a2ui-state.yaml` — no new derivation op is being added;
  an existing general-purpose one is reused for a booking use case that
  hadn't exercised it yet.

## What this does not do

- It does not add a new transport outcome or wire syntax — see
  `spec/durable-pause-v0.1.md` for the analogous "no renderer change needed"
  argument applied to a different gap.
- It does not retrofit existing atoms (`choicebox_group`, `variant_selector`).
  That's a follow-up once the pattern is proven on the three atoms above, not
  part of this document.
