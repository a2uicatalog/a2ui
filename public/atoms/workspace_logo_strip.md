# Workspace Logo Strip

Horizontal strip of Google Workspace product logos. Greyscale by default, restores colour on hover.

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
| apps | array of app names (default gmail, drive, docs, sheets, slides, meet) |
| title | optional label above the strip |
| size | logo size in px (default 40) |
| gap | gap between logos (default 24px) |
| greyscale | render greyscale until hover (default true) |
| bg | strip background colour (default transparent) |
| align | flex-start (default), center, flex-end |

## Example payload

```json
{
  "type": "workspace_logo_strip"
}
```

Live page: https://a2uicatalog.ai/atoms/workspace_logo_strip/
Full field contract: https://a2uicatalog.ai/spec.json
