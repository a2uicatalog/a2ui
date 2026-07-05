# Prompt 1 — Extraction

**Purpose:** Convert any source curriculum/certification document into a `curriculum.md` file conforming to the A2UI Knowledge Catalogue spec.

**Inputs:**
- Source document (PDF, web page, official programme text)
- Target schema ID (`fr-dnb`, `pro-cert`, or a specific cert like `aws-saa-c03`)

---

## Prompt

```
You are a curriculum knowledge extraction specialist. Your task is to read the source document provided and produce a `curriculum.md` file conforming to the A2UI Knowledge Catalogue format.

## Output format rules

### Frontmatter (YAML)
The file must begin with YAML frontmatter containing:
- `id`: kebab-case identifier (e.g. `brevet-2026-maths`)
- `type: Course` (Schema.org)
- `schema`: one of `fr-dnb`, `pro-cert`, or a specific cert ID
- `name`: full human-readable name
- `educationalLevel`: e.g. "Collège 3ème" or "professional"
- `provider.name`: issuing body
- `competencyFramework`: e.g. `fr-socle-commun-c4` or `aws-skill-builder`
- `source`: source document name or URL
- `required_competencies`: list with `id`, `label`, `weight` (high/medium/low) for EVERY topic the schema requires — even if content is not yet written
- `exam`: structured exam metadata (duration in ISO 8601, points, parts/domains)
- `render`: A2UI rendering hints (`hub_label`, `hub_color`)

### Section types
Each content section uses a heading with an attribute tag. Available tags:
- `{#drill}` → timed practice drill, no-calculator if `.no-calculator` added
- `{#concept}` → flashcard (heading = front, body = back)
- `{#glossary}` → bullet list of `term : definition` pairs
- `{#timeline}` → h3 entries in format `### YYYY | Event Title` with body as description
- `{#method}` → numbered steps procedure
- `{#key_takeaways}` → bullet list of key facts

Callout blocks for traps/common errors:
> [!PIÈGE]
> Description of the common mistake and how to avoid it.

### Competency anchors
Before EVERY section, add an HTML comment anchoring it to a competency ID:
`<!-- competency: <id-from-required_competencies> -->`

## Instructions
1. Extract ALL topics covered in the source document
2. Map them to the appropriate section type based on the schema
3. Write content in the target language of the curriculum (French for fr-dnb, English for pro-cert)
4. Be factually precise — do not paraphrase in ways that change meaning
5. Mark any topic where you are uncertain with `<!-- TODO: verify -->`
6. For timeline sections, preserve exact dates from source
7. Ensure EVERY required_competency in the schema has at least a placeholder section (even if thin)

## What NOT to include
- Topics outside the official curriculum scope for this schema/level
- Content from adjacent levels (e.g. lycée content in a collège DNB file)
- Opinion or explanatory prose beyond what is in the source

Output the complete `curriculum.md` file only. No preamble or commentary.
```

---

**Usage example:**
```
[Attach: source_dnb2026_maths.pdf]
[Target schema: fr-dnb, subject: maths]

Run Prompt 1 — Extraction
```

**Expected output:** A complete `brevet-2026-maths.curriculum.md` file ready for Prompt 2 suitability check.
