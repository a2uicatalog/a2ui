# Person Card

Individual person card with name, role, optional photo, bio, tags, and contact links. Use inside a columns atom to build team rosters.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string (required) |
| role | string (optional) |
| photo_url | string (optional, URL) |
| bio | string (optional, markdown) |
| email | string (optional) |
| linkedin | string (optional, URL) |
| tags | string[] (optional) |
| accent | string (optional, hex, default "#6366f1") |

## Example payload

```json
{
  "type": "person_card",
  "name": "Person Card"
}
```

Live page: https://a2uicatalog.ai/atoms/person_card/
Full field contract: https://a2uicatalog.ai/spec.json
