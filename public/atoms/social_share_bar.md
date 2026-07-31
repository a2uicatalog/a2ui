# Social Share Bar

Displays a row of quick-action buttons enabling readers to share the post to external networks.

## Surfaces

web, google-apps-script-web, mcp-apps

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
