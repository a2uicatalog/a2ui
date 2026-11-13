# Word Cloud

Interactive word cloud — static words or live Google Sheets feed with submit input

## Surfaces

google-apps-script-web, mcp-apps, android

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
| words | array of {text, weight} (optional static words) |
| palette | array of hex strings (optional, word colours) |
| placeholder | string (optional, input placeholder) |
| accent | string (optional, hex accent for input bar) |
| sheet_url | string (optional, Google Sheet CSV URL for live words) |
| write_url | string (optional, GAS doGet URL to write submissions) |
| poll | number (optional, poll interval seconds) |

## Example payload

```json
{
  "type": "word_cloud"
}
```

Live page: https://a2uicatalog.ai/atoms/word_cloud/
Full field contract: https://a2uicatalog.ai/spec.json
