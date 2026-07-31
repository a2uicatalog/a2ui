# Cursor Glow

Ambient radial gradient orb that smoothly lerp-follows the cursor across the page using requestAnimationFrame. Uses CSS mix-blend-mode:screen for a light-leak feel. Page-scoped and double-init guarded.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| colour | string (optional). Orb colour. Default |
| size | integer (optional). Orb diameter in px. Default 380. |
| opacity | number (optional). Orb opacity 0–1. Default 0.18. |
| speed | number (optional). Lerp factor 0–1 — lower = more lag. Default 0.1. |
| blend | string (optional). CSS mix-blend-mode. Default screen. |

## Example payload

```json
{
  "type": "cursor_glow"
}
```

Live page: https://a2uicatalog.ai/atoms/cursor_glow/
Full field contract: https://a2uicatalog.ai/spec.json
