# Social Share Bar

Displays a row of quick-action buttons enabling readers to share the post to external networks.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| platforms | array. Permitted networks: twitter | linkedin | facebook | reddit. |
| url | string. Optional URL override, defaults to current page. |

## Example payload

```json
{
  "type": "social_share_bar",
  "platforms": [
    "twitter",
    "linkedin",
    "facebook"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/social_share_bar/
Full field contract: https://a2uicatalog.ai/spec.json
