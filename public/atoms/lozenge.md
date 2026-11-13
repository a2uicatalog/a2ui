# Lozenge

Atlassian Design System semantic status pill with six strictly defined appearance variants — default (grey), success (green), removed (red), inprogress (blue), moved (yellow), new (teal). Uppercase rounded-rectangle label. Distinct from badge_group which uses arbitrary colours; lozenge maps to Jira/Confluence status semantics. Adapted from Atlassian Design System Lozenge component.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android

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
| text | string. The lozenge label (single lozenge mode). |
| appearance | string (optional). One of default | success | removed | inprogress | moved | new. Default default. |
| items | array (optional). List of {text, appearance} for a row of multiple lozenges. Overrides single text/appearance fields. |

## Example payload

```json
{
  "type": "lozenge",
  "text": "New"
}
```

Live page: https://a2uicatalog.ai/atoms/lozenge/
Full field contract: https://a2uicatalog.ai/spec.json
