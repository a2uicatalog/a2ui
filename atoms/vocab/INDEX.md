---
title: A2UI Vocabulary Index
total_atoms: 273
source: atoms/schema.yaml
generated: 2026-06-17
usage: Load this file at the start of any agent session to give Gemini full vocabulary awareness.
---

# A2UI Vocabulary Index

**273 atoms** across 13 categories. Surface key: **bold** = full support · `*` = degraded · omitted = incompatible.

## How to use this vocabulary

1. Every page is a JSON object: `{ "title": "...", "theme": "light|dark", "blocks": [...] }`
2. Each block is `{ "type": "<atom_type>", ...fields }`
3. Check surface support before using an atom — GAS Web App has the broadest support
4. Atoms marked `workspace_native` only work in GAS Web App (they use Apps Script server APIs)

## Surface codes

| Code | Surface |
|------|---------|
| `google-apps-script-web` | Google Apps Script Web App |
| `web` | Web/Blog (Google Sites HTML) |
| `meet-stage` | Meet Stage |
| `googlechat` | Google Chat card |

## Category index

| Category | Atoms | GAS | Web | Meet | Chat |
|----------|-------|-----|-----|------|------|
| [Content & Typography](content.md) | 27 | 27 | 27 | 18 | 9 |
| [Lists, Tables & Structure](lists_and_structure.md) | 28 | 28 | 28 | 19 | 1 |
| [Code & Technical Reference](code_and_technical.md) | 21 | 21 | 21 | 7 | 0 |
| [Media & Embeds](media_and_embeds.md) | 24 | 15 | 24 | 15 | 3 |
| [Data, Charts & Metrics](data_and_charts.md) | 34 | 34 | 34 | 30 | 3 |
| [Interactive UI & Forms](interactive_and_ui.md) | 38 | 38 | 38 | 32 | 1 |
| [Learning & Gamification](learning_and_gamification.md) | 13 | 13 | 13 | 8 | 1 |
| [Social & Content Marketing](social_and_content_marketing.md) | 21 | 20 | 21 | 9 | 0 |
| [Layout & Page Components](layout_and_page.md) | 25 | 25 | 25 | 20 | 6 |
| [Animation & Visual Effects](animation_and_effects.md) | 26 | 25 | 26 | 22 | 0 |
| [Workspace-Native (Apps Script only)](workspace_native.md) | 6 | 6 | 0 | 0 | 0 |
| [3D & Advanced Visualisation](three_d_and_advanced.md) | 4 | 4 | 4 | 4 | 0 |
| [AI & Agent Components](ai_and_agent.md) | 7 | 7 | 7 | 7 | 2 |

## Minimal schema example

```json
{
  "title": "My Page",
  "theme": "dark",
  "blocks": [
    { "type": "heading", "level": 1, "text": "Hello World" },
    { "type": "body", "text": "Built with **A2UI**." },
    { "type": "stat_card", "value": "273", "label": "Atoms available", "accent": "#6366f1" },
    { "type": "cta_button", "label": "Open generator →", "url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec" }
  ]
}
```

## Adding a new atom

1. Add the renderer function to the relevant `.gs` file (e.g. `atoms_globe.gs` for 3D/advanced)
2. Add the atom definition to `atoms/schema.yaml` with `works_on` surface list
3. Run `python3 scripts/gen_vocab.py` to regenerate this bundle
4. Run `./deploy.sh "add: <atom_type>"` to deploy