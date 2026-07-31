# Expert Endorsement

Renders an endorsement from an industry expert, including their quote,

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| quote | string |
| expert_name | string |
| expert_title | string |
| expert_organization | string |
| expert_avatar_url | string |

## Example payload

```json
{
  "type": "expert_endorsement",
  "quote": "The vocabulary IS the discovery layer.",
  "expert_name": "Expert name",
  "expert_title": "Expert title",
  "expert_organization": "Expert organization",
  "expert_avatar_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/expert_endorsement/
Full field contract: https://a2uicatalog.ai/spec.json
