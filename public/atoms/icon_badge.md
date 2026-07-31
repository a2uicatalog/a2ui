# Icon Badge

Material Symbol icon inside a coloured circular badge. Good for stat rows and feature lists.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | icon ligature name (required) |
| icon_size | icon size in px (default 24) |
| bg | badge background colour (default var(--a2ui-accent)) |
| color | icon colour (default |
| padding | badge padding (default 12px) |
| radius | badge border radius (default 50%) |
| filled | filled icon variant (default false) |
| label | optional caption below |

## Example payload

```json
{
  "type": "icon_badge",
  "name": "Icon Badge"
}
```

Live page: https://a2uicatalog.ai/atoms/icon_badge/
Full field contract: https://a2uicatalog.ai/spec.json
