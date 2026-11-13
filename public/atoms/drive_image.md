# Drive Image

Embeds a Google Drive image by file ID or share URL, converting it to the correct export URL that works inside GAS iframes.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| url | Drive share URL OR file ID |
| id | alias for url |
| alt | alt text for accessibility |
| caption | caption text shown below image |
| rounded | boolean (default true) — rounded corners |
| width | CSS width string (default "max-width:100%") |

## Example payload

```json
{
  "type": "drive_image",
  "url": "https://example.com",
  "id": "https://example.com",
  "alt": "Descriptive alt text for this image",
  "caption": "A descriptive caption"
}
```

Live page: https://a2uicatalog.ai/atoms/drive_image/
Full field contract: https://a2uicatalog.ai/spec.json
