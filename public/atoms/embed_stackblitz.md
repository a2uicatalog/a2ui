# Embed Stackblitz

Renders an integrated live development engine frame executing StackBlitz workspace code.

## Surfaces

web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| project_id | string. Folder identity indicator for active workspace. |

## Example payload

```json
{
  "type": "embed_stackblitz",
  "project_id": "Project id"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_stackblitz/
Full field contract: https://a2uicatalog.ai/spec.json
