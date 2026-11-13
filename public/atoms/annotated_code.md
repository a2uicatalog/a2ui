# Annotated Code

Code block with numbered yellow callout bubbles on specific lines, with an explanation list below.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
