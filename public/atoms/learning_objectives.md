# Learning Objectives

Displays a checklist-style panel outlining competencies a reader will gain from the content.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| objectives | array. Statements describing individual knowledge achievements. |

## Example payload

```json
{
  "type": "learning_objectives",
  "objectives": [
    "Understand the core concept",
    "Apply it in practice",
    "Evaluate the results"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/learning_objectives/
Full field contract: https://a2uicatalog.ai/spec.json
