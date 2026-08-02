# Atom Anatomy

Side-by-side panel showing a rendered atom alongside its raw JSON schema

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional, panel header) |
| schema | object (atom block JSON to render and display) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "atom_anatomy",
  "schema": "{\"type\": \"example\", \"value\": \"1,234\"}"
}
```

Live page: https://a2uicatalog.ai/atoms/atom_anatomy/
Full field contract: https://a2uicatalog.ai/spec.json
