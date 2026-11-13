# Code

Fenced code block

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, claude-code, android, slides, pptx

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
| content | string |

## Example payload

```json
{
  "type": "code",
  "language": "json",
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/code/
Full field contract: https://a2uicatalog.ai/spec.json
