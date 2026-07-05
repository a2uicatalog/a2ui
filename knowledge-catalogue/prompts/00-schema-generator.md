# Prompt 0 — Schema Generator

**Purpose:** Convert an official curriculum document (national programme, exam blueprint, certification spec) into a schema YAML file. This schema becomes the authoritative source of truth for what "complete" means — it feeds both Prompt 1 (as context) and Prompt 2 (as the validation target).

**Run once per qualification.** Re-run when the official curriculum is updated.

**Inputs:**
- Official curriculum document (PDF, official programme text, exam blueprint)
- Schema ID to generate (e.g. `fr-dnb`, `aws-saa-c03`, `fr-bac-maths`)
- Target output path: `schemas/<schema-id>.yaml`

---

## Prompt

```
You are a curriculum schema architect. Your task is to read the official curriculum or exam specification document provided and produce a schema YAML file for the A2UI Knowledge Catalogue.

The schema YAML defines what a COMPLETE and ACCURATE curriculum.md must contain for a given qualification. It is the machine-readable distillation of the official programme — not course content, but the specification of required competencies.

## Output structure

```yaml
id: <schema-id>                    # kebab-case, e.g. fr-dnb or aws-saa-c03
name: "<Full qualification name>"
description: "<One sentence description>"
country: <ISO 3166-1 alpha-2>      # e.g. FR, US, EU
issuer: "<Issuing body name>"
source: "<Document name or URL>"
last_updated: "<YYYY-MM-DD if known>"

render_strategy: subject_hub       # subject_hub for academic | domain_hub for pro cert
hub_tab_order: [subject1, subject2, ...]  # academic: subjects | pro cert: omit (auto by weight)

subjects:                          # use 'subjects' for academic, 'domains' for pro cert
  <subject_id>:
    label: "<Display label>"
    hub_icon: "<emoji>"
    hub_color: "<hex>"
    exam:
      duration: <PT format>        # ISO 8601, e.g. PT2H, PT20M
      total_points: <int>
      parts:
        - id: <part_id>
          name: "<Part name>"
          duration: <PT format>
          points: <int>
          constraints: [...]       # no-calculator, timed-removal, calculator-non-programmable
          note: "<important exam rule>"
    required_competencies:
      - id: <subject>-<category>-<topic>   # kebab-case, namespaced by subject
        label: "<What must be covered>"
        weight: high|medium|low    # high = likely tested, low = edge case
        atom_hint: <type>          # drill|concept|glossary|timeline|method|key_takeaways
    forbidden:
      - id: <topic-id>
        label: "<Topic name>"
        reason: "<Why it must NOT appear — wrong level, wrong subject, etc.>"
```

## Extraction rules

### For required_competencies:
1. Extract EVERY topic, skill, or knowledge item the official document states is examinable
2. Group by subject/domain — use consistent kebab-case IDs namespaced by subject (e.g. `maths-geometrie-pythagore`)
3. Assign weight based on:
   - `high`: explicitly listed as a key skill, frequently examined, or carries significant marks
   - `medium`: mentioned in the programme but less frequently tested
   - `low`: edge cases, optional enrichment, or rarely examined
4. Assign atom_hint based on content type:
   - Facts/formulas to memorise → `drill` or `glossary`
   - Theorems/concepts with proof → `concept`
   - Chronological events → `timeline`
   - Step-by-step procedures → `method`
   - Exam structure info → `key_takeaways`

### For forbidden:
1. Extract any topics explicitly excluded in the document ("hors programme", "lycée uniquement", etc.)
2. Add any topics you know from domain expertise are adjacent but out of scope for this level
3. Be conservative — only add `forbidden` entries you are confident about

### For exam structure:
1. Extract exact durations, point values, and constraints from the document
2. Use ISO 8601 for all durations (PT2H = 2 hours, PT20M = 20 minutes)
3. Capture special rules (calculator prohibition, timed removal of question sheets, etc.)

### Competency ID naming convention:
- Academic: `<subject>-<category>-<specific-topic>`
  - e.g. `maths-geometrie-pythagore`, `fr-grammaire-figures-style`
- Pro cert: `<vendor-abbrev>-<service-or-domain>-<specific-topic>`
  - e.g. `aws-iam-roles`, `gcp-gke-autoscaling`

## What NOT to include:
- Course content, explanations, or examples — those belong in curriculum.md, not the schema
- Topics from adjacent qualifications (e.g. bac content in a DNB schema)
- Pedagogical advice or teaching methodology

## Validation before output:
- Every required_competency must have a unique ID within the schema
- IDs must be consistent in style (all kebab-case, all namespaced)
- No competency should appear in both required_competencies and forbidden
- Atom hints must be one of: drill, concept, glossary, timeline, method, key_takeaways

Output the complete schema YAML only. No markdown fences, no commentary.
Write directly to: schemas/<schema-id>.yaml
```

---

**Usage example:**
```
[Attach: BREVET_2026_CURRICULUM.md]
[Schema ID: fr-dnb]
[Output: schemas/fr-dnb.yaml]

Run Prompt 0 — Schema Generator
```

**Expected output:** `schemas/fr-dnb.yaml` with all subjects, required competencies, exam structure, and forbidden list.

**When to re-run:** When the official curriculum document is updated (new BO, new exam blueprint, new certification version). The schema diff tells you exactly which competencies were added, removed, or reweighted — and every existing curriculum.md can be re-validated against the new schema automatically via Prompt 2.

**Relationship to other prompts:**
- Schema is INPUT to Prompt 1 (tells the extractor what to look for)
- Schema is INPUT to Prompt 2 (tells the checker what must be present)
- Schema is INPUT to Prompt 3 (tells the transformer how to organise the hub)
