# Prompt 1 (generic-demo variant) — Extraction

**Purpose:** Convert an ARBITRARY, unclassified public document (any URL,
paste, or upload — no known qualification/certification structure) into a
`curriculum.md` file conforming to the A2UI Knowledge Catalogue format,
using the `generic-demo` schema.

**Why this is a separate prompt, not a schema-conditional branch of
`01-extraction.md`:** the base prompt asks the model to invent
`required_competencies` and an `exam:` block — meaningful for a real
curriculum/cert, but pure fabrication for an arbitrary document with no
exam structure at all. `01b-grounding-check.md` exists specifically because
a live 2026-07-14 run of the base prompt invented an `exam:` block for a
document with no exam content. Reducing what the model is invited to
fabricate is itself part of the frugal-ops discipline this demo showcases —
this variant asks for strictly less than the base prompt, never more.

**Inputs:**
- Source document (arbitrary text — URL fetch result, pasted text, or
  client-extracted file text)

---

## Prompt

```
You are a document structuring specialist. Your task is to read the source
text provided and produce a `curriculum.md` file conforming to the A2UI
Knowledge Catalogue format — structuring what is actually in the source,
inventing nothing about its structure.

## Output format rules

### Frontmatter (YAML)
The file must begin with YAML frontmatter containing exactly:
- `id`: kebab-case identifier derived from the document's own title/subject
- `schema: generic-demo`
- `subject: general`
- `name`: a short human-readable title for the document
- `source`: source URL or "user-submitted" if pasted/uploaded

Do NOT include `required_competencies`, `exam`, `educationalLevel`,
`provider`, `competencyFramework`, or `render` — this schema has none of
these and any of these fields would be fabricated, not extracted.

### Section types
Each content section uses a heading with an attribute tag. Use ONLY the
tags that genuinely fit content present in the source — do not invent
sections to fill out a template:
- `{#concept}` → a distinct idea/topic (heading = the idea, body = its
  explanation)
- `{#glossary}` → bullet list of `term : definition` pairs, only if the
  source defines terms
- `{#drill}` → a markdown table of `| Question | Answer |` pairs, only if
  the source poses actual question/answer content
- `{#timeline}` → h3 entries `### YYYY | Event Title` with body as
  description, only if the source has genuinely dated events
- `{#method}` → numbered steps, only if the source describes a procedure
- `{#key_takeaways}` → bullet list of key facts, at most one such section,
  summarizing points the source actually states

Callout blocks for traps/common misconceptions the source explicitly warns
about (do not invent a trap the source doesn't mention):
> [!PIÈGE]
> Description of the misconception and the correction, as stated in source.

### Competency anchors
Omit entirely — `generic-demo` has no competency framework. Do not add
`<!-- competency: ... -->` comments.

## Instructions
1. Extract only topics genuinely present in the source document
2. Use as few section kinds as the content honestly supports — a short
   source may only warrant one or two sections total
3. Write content in the source document's own language
4. Be factually precise — do not paraphrase in ways that change meaning
5. Mark any topic where you are uncertain with `<!-- TODO: verify -->`
6. For timeline sections, preserve exact dates from source; do not include
   a timeline section at all if the source has no dated events

## What NOT to include
- Any structure not evidenced in the source (exam metadata, competency
  weights, a curriculum framework)
- Opinion or explanatory prose beyond what is in the source
- A section for every available kind just to look complete — thin/invented
  content is worse than a shorter, honest document

Output the complete `curriculum.md` file only. No preamble or commentary.
```

---

**Usage example:**
```
[Source text: fetched from https://example.com/some-article or pasted/uploaded text]

Run Prompt 1 (generic-demo variant) — Extraction
```

**Expected output:** A `curriculum.md` file using `schema: generic-demo`,
`subject: general`, ready for `01b-grounding-check.md` and then
`bom_emitter`/its JS twin with `schemas/generic-demo.yaml`.
