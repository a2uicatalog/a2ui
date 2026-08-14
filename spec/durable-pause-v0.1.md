# Durable pause — Action Contract Extension v0.1

**Status:** Draft v0.1 (2026-08-14)
**Applies to:** any wired action whose effect a human must authorise, or which
cannot complete until someone decides something.
**Requires no renderer change.** That is the main finding of this document —
see "Why this needs no new transport outcome".

## Why

A2UI wired actions have exactly two outcomes: they run, or they fail. There is
no third state for *"this is waiting on a person"*. Every consent flow in this
estate is therefore either absent or hand-built, and the hand-built one
(maison's layout draft) had to rediscover the rule below by shipping a page
that did not work.

The neighbouring ecosystem has two different mechanisms here and they are worth
separating, because taking the wrong one costs a transport rewrite:

| | Where the pause lives | Survives a reload | Survives a month |
|---|---|---|---|
| **Tier 1** — in-page gate | page state | no | no |
| **Tier 2** — durable pause | externalised store | yes | yes |

Tier 1 is CopilotKit's `renderAndWaitForResponse`: the agent stops, renders a
component, waits for a click. Tier 2 is the AG-UI field guide's *"the token is
parked, durably, for a minute or a month"* — process-execution semantics, where
the run is suspended in state that outlives every page that observed it.

**We want Tier 2, and we already have one instance of it.** `maison`'s
`layout.save_pending` / `load_pending` / `clear_pending` parks a proposed form
change keyed by `(page, who)`, discovers it at page-build time, and resumes it
when the owner presses Apply. It survives reloads and devices. It was written
for one case and never generalised.

## The load-bearing constraint

**A durable pause cannot be wired.**

The natural instinct is `visible: "#act.isAwaitingConsent"`, and it is wrong for
exactly the reason `visible: "#draft.isSuccess"` was wrong on 2026-08-14: a
wire is a claim about something that happened in *this page*. It resolves false
on a fresh load, so a real parked decision renders `display:none` and becomes
unreachable — the page is not merely stale, it actively hides the thing it
exists to show.

The rule this estate already wrote down covers it exactly:

> What the engine cannot know, the server must say.

So the gate is **discovered at build time and baked into the payload**, the same
way `has_pending` is. No wire, no expression, no cleverness.

## Why this needs no new transport outcome

The obvious design — a third envelope outcome beside `ok` and `error` — is a
trap. `{ok: true, parked: {...}}` reads to any renderer that does not know the
field as an ordinary success: the button goes green and the work never
happened. That is the silent class this repo keeps being bitten by, and it
would ship to every existing consumer at once.

It is also unnecessary. `paint_result` already exists: an action may answer with
a whole surface and the view repaints (`A2UIState.html`, and the absence of
`window._A2UI_PAINT` is a DECLARED error, never a silent no-op). A server that
wants consent parks the decision and answers with a surface containing the
gate.

**So the entire mechanism is server-side.** No new wire prop, no new envelope
field, no renderer release, nothing to hand-sync between repos — which given
this estate's history with hand-synced lists (`MCP_VERBS`, `training_parser`,
the four frozen renderer copies) is worth more than the elegance of a dedicated
outcome.

## Shape

### 1. The parked record

Persisted server-side, one collection. Fields the maison prototypes already
prove necessary:

```yaml
parked_decision:
  id:          "<scope>:<subject>:<who>"   # the KEY decides re-entrancy — see below
  verb:        "snag:delete"               # what runs on approval
  payload:     {...}                       # the arguments, frozen at park time
  prompt:      "Delete \"Tap drips\"? This cannot be undone."
  who_may:     "curtis@krygier.fr"         # who is allowed to decide
  parked_at:   "2026-08-14T15:00:00Z"
  expires_at:  "2026-08-14T15:15:00Z"      # optional
```

Two properties carried over from `snag:undo_create`, both learned the hard way:

- **The key is a pointer, not a queue.** maison's undo is per-user and
  *consumed*; under a bare "most recent" rule the second press silently acted
  on the wrong record. A parked decision must be addressable, so approving one
  cannot approve another.
- **Expiry is a refusal, not a cleanup job.** An expired decision must say it
  expired. Deleting it silently makes an approved action vanish with no account
  of why.

### 2. Discovery at build time

The surface builder asks the store what is parked for this viewer, exactly as
maison computes `has_pending`, and emits the gate into the payload. Absent
that, the page is built as normal.

### 3. Resume

One verb, `<domain>:decide`, taking the parked id and the decision. On approve
it runs the frozen payload through the ordinary dispatcher — so the verb's own
role checks and validation still apply, and a parked decision cannot become a
way around them. On decline it consumes the record and says so.

### 4. Re-entrancy

Parking the same `(scope, subject, who)` twice replaces rather than appends.
Two gates for the same decision is how a person approves something twice.

## Provenance, and what is deliberately not taken

**Taken:** the durable-pause *semantics* — a decision parked in externalised
state, discovered on any later load, resumable after a crash — from AG-UI's
human-in-the-loop framing and CopilotKit's `renderAndWaitForResponse`.

**Not taken:** the transport. AG-UI's reference implementation is SSE, and its
own field guide is candid about the cost: SSE has no backpressure (a slow
client means the server buffers), no replay without `Last-Event-ID` plus a
monotonic event id and a retention buffer, no ordering guarantee across
emitters, and no idempotency — replay plus at-least-once delivery renders
appended components twice.

**The finding: durable pause is orthogonal to streaming.** The durability comes
from externalised state, not from the socket. The two are bundled in AG-UI's
material because its demo is SSE-based. A2UI can therefore have the valuable
half over plain request/response, with no replay buffer, no backpressure
handling and no reconnection semantics at all.

That is not a shortcut. On the field guide's own account, the externalised
state IS the mechanism and the stream is a projection of it — which is the same
position `spec/a2ui-state.yaml`'s derivation boundary already takes, reached
independently and earlier.

## Increment 1: `gate_open` / `gate_close`

Tier 1 ships first, shaped so the server can supply the decision later rather
than needing replacement.

It is a **flat structure primitive pair**, like `row_open`/`row_close` and
`group_open`/`group_close` — handled in `atoms_wired_render.gs`, not an entry
in `atoms/schema.yaml`, and not a member of any catalog. (Structure primitives
have never been registered as atoms; they are renderer vocabulary. Worth noting
that this convention is undocumented outside the renderer source itself, which
is a real gap and not one this document fixes.)

```json
{"atom": "gate_open", "props": {"prompt": "Delete \"Tap drips\"?",
                                "detail": "This cannot be undone.",
                                "tone": "danger",
                                "decision_id": "park-123"}},
{"id": "yes", "atom": "ripple_button", "props": {"label": "Yes, delete"},
 "wire": {"onClick": "#delete.run"}},
{"id": "no",  "atom": "ripple_button", "props": {"label": "Cancel"},
 "wire": {"onClick": "#dismiss.run"}},
{"atom": "gate_close"}
```

`decision_id` lands on the frame as `data-decision-id`. In Tier 1 the host
mints it per page; in Tier 2 the server supplies the id of a parked record.
Nothing about the markup changes between the two.

**Why flat rather than one atom.** A single `confirm_gate` atom owning both
buttons was built on 2026-08-14 and replaced the same day. One element holding
two buttons makes the binder's `querySelector('button')` ambiguous, so it
needed two new output wire props (`onConfirm`, `onCancel`) to disambiguate —
a permanent addition to the engine's vocabulary, and to every gate that reads
it, solving a problem that existed only because the buttons had been grouped.
Flat keeps each button a top-level layout element binding through the ordinary
`onClick`, which is the same argument that makes `row_open` flat: a container
takes its contents out of the layout the binder walks.

What the wrapper still buys over loose composition is that **the pairing stays
checkable**. A `gate_open` span containing fewer than two wired buttons is a
gate the reader cannot decline, and that is decidable from the payload — a
rule for `wirecheck` in consuming apps.

What Tier 1 must NOT do is express its pending state as a wire on the acting
action, because that is precisely the shape Tier 2 cannot use.

## Open questions

- **Notification.** A decision parked for a month is only useful if someone
  learns it is waiting. Out of scope here; probably belongs with the calendar
  and Sheets integrations rather than in the action contract.
- **Multi-party approval** (two people must agree) is deliberately excluded.
  `who_may` is a single principal in v0.1.
- **Whether `parked_decision` belongs in `a2ui-storage.yaml`** as a declared
  collection shape, or stays app-owned. Leaning app-owned: the catalogue should
  not dictate a schema for the host's own store.
