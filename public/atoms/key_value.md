# Key Value

Key-value table for env vars, config options, API fields

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| items | [{'key': 'string', 'description': 'string', 'required': 'bool (optional)', 'default': 'string (optional)'}] |

## Example payload

```json
{
  "type": "key_value"
}
```

Live page: https://a2uicatalog.ai/atoms/key_value/
Full field contract: https://a2uicatalog.ai/spec.json
