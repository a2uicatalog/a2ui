# Terminal Boot

Dark terminal window that types out boot/log lines one by one

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| lines | array of strings — lines typed out in sequence |
| title | string (optional, shown as terminal header) |
| speed | number (optional, ms between lines, default 380) |

## Example payload

```json
{
  "type": "terminal_boot",
  "lines": [
    "$ npm install a2ui",
    "added 42 packages",
    "\u2713 Done in 1.2s"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/terminal_boot/
Full field contract: https://a2uicatalog.ai/spec.json
