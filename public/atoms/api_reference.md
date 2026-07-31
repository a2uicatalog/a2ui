# Api Reference

Full API/function reference block — name, description, parameters table,

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string |
| kind | function | endpoint | class | method |
| method | string (optional) |
| description | string |
| deprecated | bool (optional) |
| parameters | [{'name': 'string', 'type': 'string', 'required': 'bool (optional)', 'description': 'string', 'default': 'string (optional)'}] |
| returns | string (optional) |
| example | {'label': 'string (optional)', 'language': 'string', 'code': 'string'} |

## Example payload

```json
{
  "type": "api_reference",
  "name": "Api Reference",
  "kind": 1,
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/api_reference/
Full field contract: https://a2uicatalog.ai/spec.json
