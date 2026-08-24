# Link Button

Text hyperlink styled as a button

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| url | string |
| label | string |
| same_tab | boolean (optional). Default false (opens in a NEW tab) — right for the common case, an outbound link to somewhere that is not this app. Same opt-in chip_group already has: set true for an in-app "go to this page" link, which should behave like ordinary navigation rather than leaving a tab behind. Flipped from always-same-tab to this default 2026-08-15 after an outbound product-vendor link replaced the whole app instead of opening alongside it. |

## Example payload

```json
{
  "type": "link_button",
  "url": "https://example.com",
  "label": "Link Button"
}
```

Live page: https://a2uicatalog.ai/atoms/link_button/
Full field contract: https://a2uicatalog.ai/spec.json
