# Ripple Button

CTA button with a CSS ripple click effect. Optionally links to a URL.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | button text (required) |
| url | optional link target |
| icon | optional emoji or icon prefix |
| accent | button background colour |
| size | sm, md (default), lg |
| full_width | stretch to container width (default false) |
| align | flex-start (default), center, right |

## Example payload

```json
{
  "type": "ripple_button",
  "label": "Ripple Button",
  "accent": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/ripple_button/
Full field contract: https://a2uicatalog.ai/spec.json
