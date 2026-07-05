# A2UI Renderer — LLM Prompt

Paste this prompt into Claude, Gemini, or any capable LLM. Replace the bracketed content with your own. The output JSON pastes directly into the renderer.

---

```
You are generating a JSON payload for the A2UI renderer — a Google Apps Script app that renders structured JSON as a rich, navigable slide deck inside a Google Workspace sidebar or popup.

## Output format

Return only valid JSON. No markdown fences, no explanation.

## Top-level structure

{
  "title": "string — shown in browser tab",
  "theme": "light" | "dark",
  "blocks": [
    {
      "type": "hub",
      "subjects": [ ...Subject ]
    }
  ]
}

## Subject

{
  "id": "snake_case string",
  "label": "emoji + short label shown in nav tab",
  "color": "#hex — accent colour for this tab",
  "slides": [ ...Slide ]
}

## Slide

{
  "id": "snake_case string",
  "label": "short label for slide nav",
  "blocks": [ ...Block ]
}

## Available blocks (use 3–6 per slide)

gradient_hero       — opening hero with badge, title, subtitle, accent, accent2, align
dark_hero           — dark background hero with heading, subtext, badge, align
metric_row          — row of KPI tiles: metrics[{label, value, sub, trend: up|down|flat}]
key_takeaways       — bullet summary: points[string] (supports **bold**)
two_tone_card       — feature card: title, subtitle, accent, points[string]
risk_flag           — risks[{level: high|medium|low, title, detail}]
action_items        — items[{owner, text}]
step_progress       — progress bar: current(int), steps[{label}], accent
icon_list           — items[{icon, text}] — icon is any emoji
highlight_box       — accent: "#hex", title, body
skill_bars          — items[{label, value: 0-100, color}]
person_card         — name, role, avatar_url(optional), points[string]
flashcard_deck      — cards[{front, back}] — interactive flip cards
domain_brief        — title, badge, accent, image_url(optional), detail, areas[{label, detail}]

## Rules

- Every payload must have exactly one hub block at top level
- Every hub must have 2–5 subjects
- Every subject must have 1–3 slides
- Every slide must have 3–6 blocks
- First block of the first slide of each subject should be gradient_hero or dark_hero
- Use metric_row when presenting numbers
- Use key_takeaways as a summary block — always last on overview slides
- risk_flag levels: high = red, medium = amber, low = grey
- action_items owners: use initials (2-3 chars)
- Accent colours: use a consistent palette across the payload — pick one primary (#6366f1 indigo is a good default) and one supporting colour

## Task

Generate a payload for the following brief:

[PASTE YOUR CONTENT OR BRIEF HERE — e.g. "Q3 sprint review for a platform team. Shipped: API gateway, auth refresh. Risk: data pipeline carryover. Next sprint: pipeline first, SDK audit, fix flaky tests."]

Return only the JSON.
```

---

## Example output

See `payloads/example-team-brief.json` — a Q3 sprint review for a platform team, four subjects, twelve slides, generated from the prompt above.

## Paste into the renderer

1. Open the Apps Script deployment URL
2. The renderer reads from `?payload=` (base64) or from the hardcoded `payload` variable in `brevet_page.gs`
3. For quick testing: replace the `var payload = ...` line with your JSON
4. For URL-based: run `python3 scripts/make_url.py payloads/your-file.json` to generate the encoded URL
