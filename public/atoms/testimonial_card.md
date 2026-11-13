# Testimonial Card

Renders a single customer testimonial with text, author details, and an optional avatar.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| text | string |
| author_name | string |
| author_title | string |
| author_avatar_url | string |
| rating | integer |

## Example payload

```json
{
  "type": "testimonial_card",
  "text": "A concise description of the content.",
  "author_name": "Author Name",
  "author_title": "Author title",
  "author_avatar_url": "https://example.com",
  "rating": 75
}
```

Live page: https://a2uicatalog.ai/atoms/testimonial_card/
Full field contract: https://a2uicatalog.ai/spec.json
