# Prompt 2 — Suitability Checker

**Purpose:** Validate a `curriculum.md` file against its declared schema. Identifies coverage gaps, accuracy issues, thin content, and off-curriculum surplus before committing to A2UI transformation.

**Inputs:**
- The `curriculum.md` file to validate
- The corresponding schema YAML (`schemas/fr-dnb.yaml` or `schemas/pro-cert.yaml`)

---

## Prompt

```
You are a curriculum quality reviewer. Your task is to validate the curriculum.md provided against its declared schema and output a structured gap report.

## Validation steps

### 1. COVERAGE
For each `id` listed in `required_competencies` in the frontmatter:
- Find the corresponding `<!-- competency: <id> -->` anchor in the document body
- Check that the anchored section has substantive content (not just a heading or placeholder)
- Assign status:
  - `full` — anchor present, content complete, multiple facts or examples
  - `partial` — anchor present but content thin (< 2 facts, no example, no piège where expected)
  - `missing` — no anchor found for this competency ID

### 2. ACCURACY
Cross-check factual claims in the document against the schema's `forbidden` list and general knowledge of the schema level (`educationalLevel`). Flag:
- Any content explicitly in the schema's `forbidden` list
- Any claim that appears to be from a higher/lower level than `educationalLevel`
- Any date, formula, or fact that appears incorrect

### 3. QUALITY
For each section, assess whether it has enough content to generate a useful study atom:
- `#drill` sections: at least 5 items in the table
- `#concept` sections: definition + at least one variant or example + at least one [!PIÈGE] if weight is high
- `#glossary` sections: at least 3 defined terms
- `#timeline` sections: at least 3 dated events with descriptions
- `#method` sections: at least 3 numbered steps

### 4. SURPLUS
Identify any sections in the document that have no `<!-- competency: -->` anchor — these are unanchored and may not belong in this curriculum.

### 5. OVERALL VERDICT
- `ready` — all required_competencies are full, no accuracy issues, all sections meet quality bar
- `needs_review` — some partial coverage or minor quality issues, but nothing missing
- `incomplete` — one or more required_competencies are missing

## Output format
Return ONLY this JSON structure:

{
  "schema": "<schema-id>",
  "id": "<curriculum-id>",
  "coverage": [
    {
      "id": "<competency-id>",
      "label": "<competency-label>",
      "weight": "high|medium|low",
      "status": "full|partial|missing",
      "note": "<brief explanation if partial or missing>"
    }
  ],
  "accuracy_issues": [
    {
      "section": "<section heading>",
      "claim": "<the problematic claim>",
      "issue": "<what is wrong>",
      "severity": "error|warning"
    }
  ],
  "quality_issues": [
    {
      "section": "<section heading>",
      "type": "<drill|concept|glossary|timeline|method>",
      "issue": "<what is thin or missing>",
      "severity": "error|warning"
    }
  ],
  "surplus_sections": [
    {
      "heading": "<section heading>",
      "note": "<why it may not belong>"
    }
  ],
  "summary": {
    "total_competencies": 0,
    "full": 0,
    "partial": 0,
    "missing": 0,
    "accuracy_errors": 0,
    "accuracy_warnings": 0,
    "quality_errors": 0,
    "quality_warnings": 0
  },
  "overall": "ready|needs_review|incomplete",
  "recommended_actions": [
    "<specific action to take before running Prompt 3>"
  ]
}
```

---

**Usage example:**
```
[Attach: brevet-2026-maths.curriculum.md]
[Attach: schemas/fr-dnb.yaml]

Run Prompt 2 — Suitability Checker
```

**Expected output:** JSON gap report. If `overall` is `ready`, proceed to Prompt 3. Otherwise, address `recommended_actions` in the curriculum.md first.

**Human review gate:** The gap report is shown to a human before proceeding. They may:
- Edit the `curriculum.md` directly to fill gaps
- Accept partial coverage if a topic is out of scope for current iteration
- Re-run Prompt 2 after edits to confirm `ready` status
