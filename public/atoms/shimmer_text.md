# Shimmer Text

Headline text with an animated shimmer/gloss sweep across a gradient. Use for hero taglines.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| text | the text to render (required) |
| size | font-size CSS value (default 2rem) |
| from | gradient start colour (default |
| to | gradient end colour (default |
| via | mid shimmer colour (default |
| speed | animation cycle in seconds (default 2.5) |
| weight | font-weight (default 800) |
| align | left (default), center, right |

## Example payload

```json
{
  "type": "shimmer_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/shimmer_text/
Full field contract: https://a2uicatalog.ai/spec.json
