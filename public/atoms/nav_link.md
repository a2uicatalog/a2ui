# Nav Link

Single CTA button or link that navigates to a named A2UI page. Automatically appends &from=<current_slug> so the destination page's back button returns here. Style variants — primary (filled indigo), ghost (border), or text (minimal).

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| nav_slug | string (required). Slug of the destination named page. |
| label | string (optional). Button label. Default "Continue →". |
| icon | string (optional). Emoji or icon prefix. |
| style | string (optional). "primary" (default), "ghost", or "text". |
| align | string (optional). "left" (default), "center", or "right". |

## Example payload

```json
{
  "type": "nav_link",
  "nav_slug": "Nav slug"
}
```

Live page: https://a2uicatalog.ai/atoms/nav_link/
Full field contract: https://a2uicatalog.ai/spec.json
