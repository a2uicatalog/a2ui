# Confidence Bar

Horizontal confidence or probability bar — shows a percentage value with a label and colour-coded fill indicating certainty level. Used for classification confidence, sentiment strength, retrieval relevance scores, or any normalised probability output. Original a2ui-catalogue atom.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| label | string. What is being measured, e.g. Positive Sentiment or Retrieval Relevance. |
| value | number. Confidence percentage 0-100; a value in (0, 1] is read as a fraction (0.87 = 87%). |
| items | array (optional). List of {label, value} for multi-row display instead of single bar. |
| color | string (optional). Override bar fill colour. Auto-assigned green/amber/red by value band if omitted. |

## Example payload

```json
{
  "type": "confidence_bar",
  "label": "Confidence Bar",
  "value": 75
}
```

Live page: https://a2uicatalog.ai/atoms/confidence_bar/
Full field contract: https://a2uicatalog.ai/spec.json
