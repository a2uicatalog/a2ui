# Tag Cloud

Visual cloud of tags with variable font size based on weight. Heavier tags appear larger. Use for skill tags, topic clouds, keyword displays.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android

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
| title | string (optional) |
| accent | string (optional, default hex) |
| min_size | integer (optional, minimum font size px, default 12) |
| max_size | integer (optional, maximum font size px, default 22) |
| tags | array (required, alias items). Each: {label, weight? (default 1), color?} or plain string |

## Example payload

```json
{
  "type": "tag_cloud"
}
```

Live page: https://a2uicatalog.ai/atoms/tag_cloud/
Full field contract: https://a2uicatalog.ai/spec.json
