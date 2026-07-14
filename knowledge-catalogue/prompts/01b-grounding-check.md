# Prompt 1b — Grounding Checker

**Purpose:** Verify that `curriculum.md` (Prompt 1's output) is actually grounded in the source document — that no field, claim, or metadata value was invented to satisfy the schema template's expected shape. Runs BETWEEN Prompt 1 (Extraction) and Prompt 2 (Suitability), because Prompt 2 never sees the original source — it only checks curriculum.md against the schema, so it structurally cannot detect fabrication. This step exists because it was needed: a live bake-off (2026-07-14, free-tier Cloudflare Workers AI, `@cf/meta/llama-3.3-70b-instruct-fp8-fast`) fabricated a complete `exam:` block (duration, points, domain weights) for a source document that was pure API documentation with no exam content whatsoever — every required_competency was extracted accurately, but the exam metadata was invented purely because the schema template has an `exam:` field.

**Inputs:**
- The `curriculum.md` file to check (Prompt 1's output)
- The ORIGINAL source document Prompt 1 was given (not just the schema — this is the whole point)

---

## Prompt

```
You are a fact-checking specialist. Your task is to verify that curriculum.md's
content is GROUNDED in the source document provided — that nothing was invented
to satisfy the schema template's expected shape rather than what the source
actually says.

## What to check

### 1. FRONTMATTER METADATA — only fields that should be DERIVED FROM SOURCE
Some frontmatter fields are meant to be COPIED THROUGH from the schema
instance Prompt 1 was given, not derived from the source document — `id`,
`type`, `schema`, `competencyFramework`, `render.hub_label`,
`render.hub_color`, and each required_competency's `weight` (weights are a
schema-author judgment call, supplied as input, not something to re-derive
from source text). Do NOT flag these as unsupported just because they don't
appear verbatim in the source — that's expected and correct.

DO check fields that should be DERIVED FROM READING THE SOURCE: `exam.duration`,
`exam.points`, `exam.passing_score`, exam part/domain structure, dates, counts,
or any other administrative/quantitative metadata that claims to describe
what's IN the source material:
- Search the source document for direct textual support
- If found: record the supporting line/phrase
- If NOT found: flag as UNSUPPORTED — a value with no basis in source

If you're unsure which category a field falls into, ask: "does this field
describe something the SCHEMA AUTHOR decided, or something the SOURCE
DOCUMENT contains?" Only the latter needs grounding.

### 2. CATEGORY-LEVEL MISMATCH (check this FIRST, before line-by-line)
Some schema fields describe a whole CONTENT CATEGORY the source may not
contain at all — e.g. an `exam:` block when the source is pure reference
documentation with no assessment/exam content anywhere. If the source
contains NO content of that category, the entire field is unsupported BY
CONSTRUCTION — flag it as one item, don't check its sub-fields individually.

### 3. BODY CONTENT
For each section's substantive claims (facts, numbers, code samples,
procedures, dates, names):
- Cross-check against the source document
- Flag any claim that does not appear in source, was altered in a way that
  changes its meaning, or reads more specific/complete than what the source
  actually states (a common pattern: the model fills in a plausible-sounding
  detail the source never gave)

### 4. CODE SAMPLE FIDELITY
For any code block: confirm it matches the source's code sample structure
(method names, parameter shapes, control flow) — not just similar-looking
code the model reconstructed from general knowledge of the API.

## Output format
Return ONLY this JSON structure:

{
  "grounded_fields": [
    {"field": "<field path>", "support": "<quoted or paraphrased source text that supports it>"}
  ],
  "unsupported_fields": [
    {"field": "<field path>", "value": "<the fabricated value>",
     "reason": "no basis found in source|source contains no content of this category"}
  ],
  "altered_claims": [
    {"section": "<heading>", "claim": "<what curriculum.md says>",
     "source_says": "<what the source actually says, or 'nothing' if absent>",
     "issue": "<how it was altered/invented>"}
  ],
  "overall": "grounded|has_fabrication",
  "recommended_actions": [
    "<e.g. remove the exam: block entirely — source contains no exam content>"
  ]
}
```

---

**Usage example:**
```
[Attach: chat_api_curriculum_70b.md]
[Attach: chat_api_source.md]

Run Prompt 1b — Grounding Checker
```

**Expected output:** JSON grounding report. If `overall` is `has_fabrication`,
fix curriculum.md (usually: delete the unsupported field/block, or mark it
`<!-- TODO: verify against source -->` if partially supported) before running
Prompt 2. This is a SEPARATE gate from suitability — a curriculum.md can be
fully `ready` on coverage (Prompt 2) while still containing fabricated
metadata, because coverage checks completeness against the schema, not
truthfulness against the source.

**Mandatory post-processing — do not trust the model's own categorization
here.** Live-tested (2026-07-14, free-tier `llama-3.3-70b-instruct-fp8-fast`):
the model correctly EXPLAINED in its own reasoning text that `weight` is "a
schema-author judgment call, not derived from source" — using almost the
exact wording of the instruction above — and then still listed it under
`unsupported_fields` anyway, contradicting its own stated reasoning in the
same response. It also re-flagged `id`/`type`/`schema`/`competencyFramework`
despite being told explicitly not to. A model can articulate a rule
correctly in prose while failing to apply it to its own output — whoever
runs this step (human or agent) MUST mechanically strike any
`unsupported_fields` entry whose `field` is one of `id`, `type`, `schema`,
`competencyFramework`, `weight` (or `required_competencies[*].weight`),
`render.hub_label`, `render.hub_color` BEFORE presenting the report, rather
than trusting the model to have excluded them itself. This is a deterministic
filter, not a re-prompt — re-prompting the same model for the same
distinction is unlikely to fix an inconsistency between its reasoning and
its categorization.

**Human review gate:** Same as Prompt 2 — the grounding report is shown to a
human before proceeding, not auto-applied. Removing a field the model
invented is usually safe to auto-accept; disputed "altered_claims" (where the
model's version might be a legitimate paraphrase) should get a human read.
