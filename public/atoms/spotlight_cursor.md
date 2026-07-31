# Spotlight Cursor

A dark overlay with a soft-edged circular cutout that follows the cursor — torch or spotlight effect. Best used as a standalone page effect or dramatic opening slide.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| radius | integer (optional). Spotlight radius px. Default 180. |
| darkness | number (optional). Overlay opacity 0–1. Default 0.82. |
| colour | string (optional). Overlay colour. Default |
| soft_edge | integer (optional). Feather distance px beyond radius. Default 60. |

## Example payload

```json
{
  "type": "spotlight_cursor"
}
```

Live page: https://a2uicatalog.ai/atoms/spotlight_cursor/
Full field contract: https://a2uicatalog.ai/spec.json
