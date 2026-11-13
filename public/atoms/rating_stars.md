# Rating Stars

A row of stars showing a rating out of a maximum, optionally marked as interactive.

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
| rating | integer The current rating value (e.g., 3 for 3 stars). |
| max_rating | integer The maximum possible rating (e.g., 5 for 5 stars). |
| is_interactive | boolean Indicates if the stars are clickable for user input. |

## Example payload

```json
{
  "type": "rating_stars",
  "rating": 75,
  "max_rating": 75,
  "is_interactive": true
}
```

Live page: https://a2uicatalog.ai/atoms/rating_stars/
Full field contract: https://a2uicatalog.ai/spec.json
