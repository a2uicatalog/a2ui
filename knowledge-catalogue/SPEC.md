# A2UI Knowledge Catalogue — Specification

**Version:** 1.0 | **Date:** 2026-06-21 | **Article topic:** A2UI Renderer Launch

> This document is the canonical spec for the A2UI Knowledge Catalogue format and ingestion pipeline. It is also the basis for the A2UI renderer launch article — demonstrating that A2UI is not just a UI renderer but a knowledge rendering platform.

---

## The Core Idea

Most study apps are one-off builds: someone hand-crafts content, exports to a format, and the app is born. The curriculum changes, the app rots.

The A2UI Knowledge Catalogue inverts this. The **curriculum is the source of truth** — structured, versioned, and schema-aware. The A2UI app is a *rendered view* of that curriculum, regeneratable on demand.

The pipeline: **Source → curriculum.md → gap report → payload.json → live app**. The only step that requires human judgment is the gap report review. Everything else is LLM-driven and deterministic.

---

## The curriculum.md Format

Every curriculum file is a single Markdown document with:

### Frontmatter (YAML)
Uses **Schema.org** vocabulary for interoperability with LMS systems (Moodle, Canvas, edX):

```yaml
---
id: brevet-2026-maths           # kebab-case unique identifier
type: Course                     # Schema.org type
schema: fr-dnb                   # parser/validator behaviour switch
name: "Mathématiques — DNB 2026"
educationalLevel: "Collège 3ème" # Schema.org
provider:
  name: "Ministère de l'Éducation Nationale"
competencyFramework: fr-socle-commun-c4  # CASE reference
source: source_dnb2026_automatismes.pdf

required_competencies:           # What a COMPLETE doc must cover
  - id: maths-geometrie-pythagore
    label: "Pythagore — direct, réciproque, contraposée"
    weight: high                 # high | medium | low

exam:                            # ISO 8601 durations
  duration: PT2H
  total_points: 20
  parts:
    - id: automatismes
      name: Automatismes
      duration: PT20M
      points: 6
      constraints: [no-calculator, timed-removal]

render:                          # A2UI-only — ignored by LMS
  hub_label: "📐 Maths"
  hub_color: "#6366f1"
---
```

### Section types
Typed headings tell the parser what A2UI atom to generate:

| Tag | Atom | Usage |
|---|---|---|
| `{#drill}` | `brevet_automatismes` | Tables of facts for timed practice |
| `{#concept}` | `flashcard_deck` | Heading = front, body = back |
| `{#glossary}` | `flashcard_deck` | Bullet `- **term** : definition` |
| `{#timeline}` | `brevet_timeline` | h3 entries: `### YYYY \| Title` |
| `{#method}` | `steps` | Numbered steps |
| `{#key_takeaways}` | `key_takeaways` | Bullet list of key facts |
| `[!PIÈGE]` callout | `knowledge_check` | Common trap + correction |

### Competency anchors
HTML comment before each section links content to a required competency:
```
<!-- competency: maths-geometrie-pythagore -->
## Théorème de Pythagore {#concept .weight-high}
```
This is the machine-readable link that enables gap detection. Invisible in rendered Markdown, trivially parseable by LLMs and Python.

---

## The 4-Prompt Pipeline

Two source documents feed the pipeline with different roles:
- **Official Curriculum** (`BREVET_2026_CURRICULUM.md`, exam blueprint PDF) → defines *what* must be covered → becomes the schema
- **Course Content** (`BREVET_2026_MANUEL.md`, textbook, study manual) → explains *how* to cover each topic → becomes curriculum.md

### Prompt 0 — Schema Generator
**Input:** Official curriculum document
**Task:** LLM extracts all required competencies, exam structure, and forbidden topics → outputs schema YAML
**Run once per qualification.** Re-run when the official programme is updated.
**Output:** `schemas/<schema-id>.yaml`

See: `prompts/00-schema-generator.md`

### Prompt 1 — Extraction
**Input:** Official curriculum + course content + schema YAML (all three)
**Task:** LLM reads course content, emits complete `curriculum.md` with frontmatter, typed sections, and competency anchors. Uses the schema as the target list and the curriculum doc as the "what to cover" guide.
**Key rule:** Every `required_competency` from the schema must have a section — even a thin placeholder.

See: `prompts/01-extraction.md`

### Prompt 2 — Suitability Checker
**Input:** `curriculum.md` + schema YAML
**Task:** LLM cross-references every `<!-- competency: id -->` anchor against `required_competencies`. Outputs structured JSON:

```json
{
  "coverage": [
    {"id": "maths-geometrie-pythagore", "status": "full", "note": ""},
    {"id": "maths-stats-probabilites", "status": "partial", "note": "Arbres de probabilité missing"}
  ],
  "accuracy_issues": [...],
  "quality_issues": [...],
  "overall": "needs_review",
  "recommended_actions": ["Add probability trees section"]
}
```

**Human gate:** Review gap report. Edit curriculum.md if needed. Re-run until `overall: ready`.

See: `prompts/02-suitability.md`

### Prompt 3 — A2UI Transformer
**Input:** Approved `curriculum.md` + schema YAML
**Task:** LLM maps each section to its A2UI atom type, builds the hub structure, outputs valid `payload.json`
**Output:** Written to `payloads/<id>.json`, fed into `make_url.py`

See: `prompts/03-transformer.md`

---

## Schema System

Schemas define what "complete" means for a given qualification type. Stored in `schemas/`.

| Schema | File | For |
|---|---|---|
| `fr-dnb` | `schemas/fr-dnb.yaml` | French DNB (brevet) — all 5 subjects |
| `pro-cert` | `schemas/pro-cert.yaml` | Generic professional cert (AWS, GCP, PMP…) |

Each schema carries:
- `required_competencies` per subject/domain — the ground truth for gap detection
- `forbidden` list — topics that look plausible but are out of scope
- `atom_type_map` — section tag → A2UI atom type
- `render_strategy` — `subject_hub` (academic) or `domain_hub` (pro cert)

**Adding a new schema:** Copy `schemas/pro-cert.yaml`, fill in `required_competencies` from the official exam blueprint.

---

## LMS Interoperability

The format deliberately borrows vocabulary from established standards so it can be exported or imported without transformation:

| Standard | Used for |
|---|---|
| **Schema.org** `Course` | frontmatter field names (`type`, `educationalLevel`, `provider`) |
| **1EdTech CASE** | competency ID scheme and `required_competencies` structure |
| **QTI-lite** | `[!PIÈGE]` → question/correct/explanation pattern |
| **ISO 8601** | exam durations (`PT2H`, `PT20M`) |

The `render:` block is the only A2UI-specific section — an LMS importer ignores it. This means `curriculum.md` files can be shared, versioned on git, and potentially imported into Moodle/Canvas without modification.

---

## Why This Matters for A2UI

The standard A2UI demo is: *"here's a JSON payload, here's the rendered atom."*

The Knowledge Catalogue demo is: *"here's a national curriculum, here's the gap analysis, here's the study app — generated end-to-end from structured knowledge."*

A2UI becomes not just a UI renderer but a **knowledge rendering platform**:
- The curriculum.md is the knowledge graph node
- The schema YAML is the validation vocabulary
- The A2UI atoms are the rendered views
- The suitability checker is the quality gate

This scales: one pipeline, any qualification — brevet, bac, AWS, GCP, PMP, DELF, driving theory. Each cert gets a schema YAML. Each subject gets a curriculum.md. The renderer is the same.

---

## File Structure

```
knowledge-catalogue/
├── SPEC.md                              ← this file (article source)
├── diagram.d2                           ← pipeline architecture (D2 source)
├── diagram.svg                          ← rendered diagram (cyberpunk theme)
├── schemas/
│   ├── fr-dnb.yaml                      ← DNB required competencies per subject
│   └── pro-cert.yaml                    ← Generic pro cert schema + examples
├── prompts/
│   ├── 01-extraction.md                 ← Prompt 1: source → curriculum.md
│   ├── 02-suitability.md                ← Prompt 2: validate coverage
│   └── 03-transformer.md                ← Prompt 3: curriculum.md → payload.json
└── examples/
    └── brevet-2026-maths.curriculum.md  ← Reference implementation
```

---

## Live Example

The brevet 2026 app was built with this pipeline (retroactively):
- Source: `BREVET_2026_CURRICULUM.md` + `BREVET_2026_MANUEL.md`
- Schema: `fr-dnb`
- Audit: `BREVET_2026_AUDIT.md` (the manual gap report that preceded this spec)
- Payload: `payloads/brevet_full.json`
- Live: `https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec?nav=brevet-2026`

The brevet audit identified 17 gaps. The `fr-dnb.yaml` schema now encodes those lessons — run the suitability checker on the brevet curriculum.md and it will catch all 17 automatically.
