# Api Reference

Full API/function reference block — name, description, parameters table, return value, and example.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
