# Cta Button

Full-width call-to-action button linking to a URL

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| url | string |
| label | string |
| color | string (optional, hex) |
| same_tab | boolean (optional). Default false (opens in a NEW tab) — see link_button's same_tab for the full reasoning; same field, same default, same atom family. |

## Example payload

```json
{
  "type": "cta_button",
  "url": "https://example.com",
  "label": "Cta Button"
}
```

Live page: https://a2uicatalog.ai/atoms/cta_button/
Full field contract: https://a2uicatalog.ai/spec.json
