# Workspace Logo Grid

Grid of Google Workspace product logos with labels. Good for "Integrations" or "Works with" sections.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| apps | array of app names (default all 20 known apps) |
| title | optional section heading |
| size | logo size in px (default 48) |
| cols | grid columns (default 5) |
| greyscale | render greyscale (default false) |
| show_labels | show app name labels (default true) |

## Example payload

```json
{
  "type": "workspace_logo_grid"
}
```

Live page: https://a2uicatalog.ai/atoms/workspace_logo_grid/
Full field contract: https://a2uicatalog.ai/spec.json
