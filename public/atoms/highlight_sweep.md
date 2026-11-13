# Highlight Sweep

Text with an animated highlight sweep underline that plays on load

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
| text | string (alias: content) |
| color | string (optional, highlight colour hex, default #fef08a yellow) |
| delay | number (optional, seconds before sweep starts) |
| size | string (optional, CSS font-size) |

## Example payload

```json
{
  "type": "highlight_sweep",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/highlight_sweep/
Full field contract: https://a2uicatalog.ai/spec.json
