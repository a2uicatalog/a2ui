# Star Rating Input

Renders an interactive star rating component for user input.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| max_stars | integer |
| initial_rating | integer |
| name | string |

## Example payload

```json
{
  "type": "star_rating_input",
  "max_stars": 5,
  "initial_rating": 75,
  "name": "Star Rating Input"
}
```

Live page: https://a2uicatalog.ai/atoms/star_rating_input/
Full field contract: https://a2uicatalog.ai/spec.json
