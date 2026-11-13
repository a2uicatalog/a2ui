# Next Step Strip

Horizontal strip of numbered next steps with optional links

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
| steps | array of {number (optional), label, detail (optional, alias: action), url (optional)} |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "next_step_strip"
}
```

Live page: https://a2uicatalog.ai/atoms/next_step_strip/
Full field contract: https://a2uicatalog.ai/spec.json
