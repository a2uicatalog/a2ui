# Json Tree Viewer

Displays a nested, expandable visual explorer for structural JSON data objects.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| data | string. The raw valid JSON string to parse and render. |

## Example payload

```json
{
  "type": "json_tree_viewer",
  "data": "{\"key\": \"value\", \"count\": 42}"
}
```

Live page: https://a2uicatalog.ai/atoms/json_tree_viewer/
Full field contract: https://a2uicatalog.ai/spec.json
