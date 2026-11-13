# Release Notes

Displays a grouped publication document containing categorised changes for a version launch.

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
| title | string. Header name for the release notice. |
| added | array. Optional new features added in this release. |
| fixed | array. Optional bugs resolved in this release. |
| changed | array. Optional modifications to existing behaviour. |

## Example payload

```json
{
  "type": "release_notes",
  "title": "Release Notes"
}
```

Live page: https://a2uicatalog.ai/atoms/release_notes/
Full field contract: https://a2uicatalog.ai/spec.json
