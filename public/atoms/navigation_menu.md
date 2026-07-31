# Navigation Menu

Multi-level horizontal navigation bar with a brand/logo slot, top-level nav items, optional dropdown submenus, and a right-aligned CTA button. First item with children renders its submenu panel open for preview. Radix NavigationMenu pattern.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| brand | string (optional). Brand name shown on the left. |
| brand_url | string (optional). URL for the brand link. |
| items | array of objects with — label, url, children (optional array of {label, url, description}). |
| cta | object (optional). {label, url} for a right-aligned call-to-action button. |

## Example payload

```json
{
  "type": "navigation_menu"
}
```

Live page: https://a2uicatalog.ai/atoms/navigation_menu/
Full field contract: https://a2uicatalog.ai/spec.json
