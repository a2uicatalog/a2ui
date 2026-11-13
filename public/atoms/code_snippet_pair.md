# Code Snippet Pair

Renders two distinct code snippets side-by-side or stacked, without

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 480); pixels differ from React (light 480); content sits 1 px lower than in React (and than 1.85.0), stable between passes; cause not isolated. A real difference, not hidden |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| left_code | string |
| right_code | string |
| language | string |
| left_label | string |
| right_label | string |

## Example payload

```json
{
  "type": "code_snippet_pair",
  "left_code": "Left code",
  "right_code": "Right code",
  "language": "json",
  "left_label": "Left label",
  "right_label": "Right label"
}
```

Live page: https://a2uicatalog.ai/atoms/code_snippet_pair/
Full field contract: https://a2uicatalog.ai/spec.json
