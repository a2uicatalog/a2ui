# Big Reveal

Large centred number or word that pops in with a spring scale animation

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
| text | string (the big value, alias: value, label) |
| sub | string (optional subtitle below, alias: subtitle) |
| color | string (optional, hex) |
| size | string (optional, CSS font-size, default 5rem) |
| delay | number (optional, seconds) |

## Example payload

```json
{
  "type": "big_reveal",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/big_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
