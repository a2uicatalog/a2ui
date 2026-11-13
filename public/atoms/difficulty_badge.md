# Difficulty Badge

Displays a small visual marker representing the technical complexity level of an article.

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
| level | string: beginner | intermediate | advanced. The target audience expertise tier. |

## Example payload

```json
{
  "type": "difficulty_badge",
  "level": 1
}
```

Live page: https://a2uicatalog.ai/atoms/difficulty_badge/
Full field contract: https://a2uicatalog.ai/spec.json
