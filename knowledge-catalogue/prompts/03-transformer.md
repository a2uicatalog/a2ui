# Prompt 3 — A2UI Transformer

**Purpose:** Convert an approved `curriculum.md` into an A2UI `payload.json` ready for `make_url.py`. Only run after Prompt 2 returns `overall: ready`.

**Inputs:**
- The approved `curriculum.md`
- The schema YAML (`schemas/<schema-id>.yaml`) for atom type mapping and hub structure
- Target output path: `payloads/<curriculum-id>.json`

---

## Prompt

```
You are an A2UI payload generator. Your task is to convert the approved curriculum.md into a valid A2UI payload JSON file.

## A2UI payload structure

The top-level structure is:
{
  "title": "<curriculum name>",
  "theme": "light",
  "blocks": [<atom objects>]
}

The primary atom is a `hub` block containing subjects (tabs) and slides.

## Section → atom mapping

Read the `atom_type_map` from the schema YAML to know which A2UI atom type each section tag maps to. Standard mappings:

| Section tag | A2UI atom type | Notes |
|---|---|---|
| `{#drill}` | `brevet_automatismes` | Table rows become question items. Add `no_calculator: true` if `.no-calculator` class present. |
| `{#concept}` | `flashcard_deck` | Heading = card front. Body = card back. [!PIÈGE] blocks become separate piège cards. |
| `{#glossary}` | `flashcard_deck` | Each `- **term** : definition` bullet → one card. front=term, back=definition. |
| `{#timeline}` | `brevet_timeline` | Each h3 `### YYYY | Title` → one event with `{date, title, desc}`. |
| `{#method}` | `steps` | Numbered list items → step objects `{label, text}`. |
| `{#key_takeaways}` | `key_takeaways` | Bullet list → items array. |
| `[!PIÈGE]` | `knowledge_check` | question = "Vrai ou Faux: <claim>", correct = false, explanation = callout body. |

## Hub structure rules

Read `render_strategy` from schema YAML:
- `subject_hub`: one hub tab per subject. Tab order from `hub_tab_order`. First slide = Épreuve (exam structure). Last slide = Pièges (aggregated from all [!PIÈGE] callouts).
- `domain_hub`: one hub tab per domain, ordered by weight descending. No Épreuve slide.

For each tab, slides are generated in section order from the curriculum.md.

## Épreuve slide (fr-dnb only)
Generate automatically from `exam` frontmatter:
- Atom type: `key_takeaways` for exam overview
- Atom type: `steps` for exam strategy (derived from exam.parts)

## Rendering hints
Read `render.hub_label` and `render.hub_color` from curriculum.md frontmatter to set tab appearance.

## Field escaping
- All string values must be valid JSON strings (escape double quotes, backslashes)
- Emoji are allowed in labels
- Use `_esc()` convention: HTML entities for < > & in text that will be rendered as HTML

## Output
Return ONLY the complete JSON payload object. No markdown fences, no commentary.
The output should be directly writable to `payloads/<curriculum-id>.json`.

Validate before returning:
- All required hub fields present (subjects, slides, pills)
- All atom blocks have required fields for their type
- No trailing commas (valid JSON)
- Slide labels are concise (< 20 chars)
```

---

**Usage example:**
```
[Attach: brevet-2026-maths.curriculum.md]
[Attach: schemas/fr-dnb.yaml]
[Output path: payloads/brevet-2026-maths.json]

Run Prompt 3 — A2UI Transformer
```

**After transformation:**
```bash
# Encode and deploy
python3 scripts/make_url.py payloads/brevet-2026-maths.json

# Or for named page route (GAS):
# 1. Copy JSON into brevet_page.gs as hardcoded payload
# 2. clasp push && clasp deploy --deploymentId <ID>
```

**Output:** `payloads/brevet-2026-maths.json` — a complete, renderable A2UI payload.
