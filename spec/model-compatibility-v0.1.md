# model_compatibility — Schema Extension v0.1

**Status:** Draft v0.1 (2026-07-08)
**Applies to:** any A2UI atom (`atoms/schema.yaml`) or MCP tool definition that
requires client-side judgment to use correctly (sizing, pagination, procedural
branching).
**Optional field.** A2UI 1.0 renderers and consumers that don't know this field
ignore it — same posture as `surfaces.degraded_on`.

## Why

Weaker models fail to operationalize procedural guidance even when it's stated
correctly in tool/atom descriptions ("paginate when the payload is large").
They read conditional instructions as documentation, not as a branch to take at
call time. This isn't a training gap closeable by better prose alone — see the
empirical case in `a2ui-private/a2uithoughts.md` (2026-07-08, Haiku +
`make_surface_url`). The fix is either (a) a tool designed so the model never
has to judge (zero-estimation primitives), or (b) exact, threshold-based
procedural rules a strict instruction-follower CAN execute even without
judgment. `model_compatibility` declares which case applies, per atom/tool,
per model.

## Shape

```yaml
model_compatibility:
  native_support:
    models: [sonnet, fable, opus]       # models that can use this atom/tool as-is
    required_capabilities:               # optional — informational, not enforced by schema tests
      procedural_reasoning: single-branch
      estimation_accuracy: 50            # 0-100, minimum reliable estimate accuracy
      instruction_following: strict

  degraded_support:
    - models: [haiku]
      compensation_strategy: procedural_thresholds   # free-text label, describes the technique
      compensation_prose: |
        EXACT PROCEDURE — follow precisely, do not estimate:
        1. Count JSON payload characters.
        2. If <=1500 chars: call directly.
        3. If 1501-3000 chars: split into 2 sections.
        4. If 3001-5000 chars: split into 3 sections.
        Do not judge. Follow rule 2-4 exactly by character count.
      degraded_as: build_multi_page_surface   # optional — name of the safer wrapper tool/atom, if one exists
      verified: true
      verification_fixture: haiku_make_surface_url_2026-07-08.json
```

Fields:
- `native_support.models` — models known to use the atom/tool correctly without
  extra guidance. Absence of `model_compatibility` entirely means "assume
  universal" (same default as atoms with no `surfaces.degraded_on`).
- `degraded_support[].models` — models that need `compensation_prose` to use
  this safely.
- `compensation_prose` — exact, deterministic, threshold-based instructions.
  Not restating the tool description in different words — testable rules a
  strict instruction-follower can execute without estimating or judging.
- `degraded_as` — if a purpose-built safer wrapper exists (e.g.
  `build_multi_page_surface` wraps `make_surface_url`'s sizing judgment),
  name it. Prefer pointing here over prose when a wrapper exists; prose is the
  fallback when no wrapper is practical.
- `verified` — **must not be hand-set to `true` without a fixture.** Tier 1
  schema tests enforce this (see Testing below).
- `verification_fixture` — filename under
  `tests/fixtures/model_verification/`, produced by a Tier 2 run.

## Testing — two tiers

**Tier 1 (pytest, every push, no network, no cost):** structural validation
only. Checks `degraded_support` entries have `compensation_prose` and a
`models` list; checks `verified: true` entries have a fixture file that
exists, parses, and records `passed: true` for every model claimed. This
tier catches drift (schema says verified, fixture missing/stale/failing) —
it does NOT itself call any model. Lives in `tests/test_schema.py`.

**Tier 2 (agent-run, on demand, live model call):** actually exercises the
compensation prose against the real model via a live Agent call — same
mechanism as the empirical tests in `a2ui-private/a2uithoughts.md`. Run
after any change to `compensation_prose`, `degraded_as`, or the wrapped
tool's behavior, and periodically to catch model-version drift (a Haiku
update could silently break prose that used to work). Not part of the
default push/CI loop — it costs tokens and is non-deterministic (external
model call), so it's a deliberate, logged action, not an automatic gate.

Declared as `verify-model-compatibility` in `ops/project-ops.yaml`
(a2ui-catalogue) — intent, not a fully-scripted unattended step, since the
live call is an agent action (spawn a real Haiku session, feed it the task +
prose, capture pass/fail), not a deterministic API script.

## Fixture format

`tests/fixtures/model_verification/<slug>.json`:

```json
{
  "atom_or_tool": "make_surface_url",
  "models_tested": ["haiku"],
  "date": "2026-07-08",
  "task_description": "Build a 4-section multi-nav guide via make_surface_url + compensation prose",
  "passed": true,
  "evidence": {
    "url_length_max": 1487,
    "render_verified": true,
    "notes": "Haiku followed the character-count thresholds exactly; no hand-written encoding fallback."
  }
}
```

`passed` is the single field Tier 1 checks. `evidence` is free-form —
whatever concretely proves the claim (URL length under ceiling, render
confirmed, no fallback script written, etc.) — kept for humans re-auditing
the claim later, not machine-checked beyond `passed`.

## Non-goals for v0.1

- No enforcement of `required_capabilities` values — informational only,
  not a validated capability taxonomy yet. That's a separate, harder spec
  (a model capability schema — vector or tiered — is an open question, see
  `a2ui-private/a2uithoughts.md` 2026-07-08).
- No runtime capability negotiation in this spec. The MCP-side
  implementation (model-conditional `server/discover` tool filtering) is a
  separate, private-repo concern (`a2ui-private/mcp-worker`) — this spec
  only defines the declarative shape atoms/tools use to describe
  compatibility, so both public atoms and private MCP tools can use the
  same vocabulary.
