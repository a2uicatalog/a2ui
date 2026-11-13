# Framed Screenshot

Renders an image within a decorative frame, simulating a device (e.g., browser, phone).

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
| image_url | string |
| alt_text | string |
| device_type | string |
| caption | string |

## Example payload

```json
{
  "type": "framed_screenshot",
  "image_url": "https://example.com",
  "alt_text": "Descriptive alt text for accessibility",
  "device_type": "Device type",
  "caption": "A descriptive caption"
}
```

Live page: https://a2uicatalog.ai/atoms/framed_screenshot/
Full field contract: https://a2uicatalog.ai/spec.json
