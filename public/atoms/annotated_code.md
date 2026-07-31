# Annotated Code

Code block with numbered yellow callout bubbles on specific lines,

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| language | string |
| code | string |
| caption | string (optional) |
| annotations | [{'line': 'integer', 'text': 'string'}] |

## Example payload

```json
{
  "type": "annotated_code",
  "language": "json",
  "code": "{\"type\": \"example\"}",
  "annotations": 1
}
```

Live page: https://a2uicatalog.ai/atoms/annotated_code/
Full field contract: https://a2uicatalog.ai/spec.json
