# Case Study Card

Structured enterprise case study card. Sections for situation narrative, key data points (label/value/note), numbered analysis questions, and an optional model answer reveal. No state required. The model answer is hidden behind a toggle button.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (required). Case study title. |
| situation | string (required). The scenario narrative. |
| data_points | array (optional). Array of {label, value, note?} metric blocks. |
| questions | array (optional). Array of question strings for analysis. |
| model_answer | string (optional). Model answer text shown on toggle. Hidden by default. |
| accent | string (optional). Accent colour for data point values. Default |

## Example payload

```json
{
  "type": "case_study_card",
  "title": "Case Study Card",
  "situation": "A startup facing rapid growth challenges."
}
```

Live page: https://a2uicatalog.ai/atoms/case_study_card/
Full field contract: https://a2uicatalog.ai/spec.json
