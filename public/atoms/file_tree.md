# File Tree

Renders a hierarchical layout displaying directory structures, folders, and individual files for software projects.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| nodes | array. Highly structured list of folder and file objects with nesting indicators. |

## Example payload

```json
{
  "type": "file_tree",
  "nodes": [
    {
      "label": "src/",
      "children": [
        {
          "label": "index.ts"
        }
      ]
    },
    {
      "label": "package.json"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/file_tree/
Full field contract: https://a2uicatalog.ai/spec.json
