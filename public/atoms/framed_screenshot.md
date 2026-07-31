# Framed Screenshot

Renders an image within a decorative frame, simulating a device (e.g.,

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
