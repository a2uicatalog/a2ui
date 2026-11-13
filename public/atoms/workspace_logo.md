# Workspace Logo

A single Google Workspace product logo from Google's official CDN (fonts.gstatic.com). Falls back to coloured letter badge for unknown apps.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| app | app name (required) — gmail, drive, docs, sheets, slides, calendar, meet, forms, chat, classroom, keep, sites, vault, groups, tasks, contacts, jamboard, admin, appsheet, currents |
| size | display size in px (default 48 — SVG scales to any size) |
| label | caption below logo (default capitalised app name; set to empty string to hide) |
| inline | render inline (default true) |

## Example payload

```json
{
  "type": "workspace_logo",
  "app": "MyWorkspace"
}
```

Live page: https://a2uicatalog.ai/atoms/workspace_logo/
Full field contract: https://a2uicatalog.ai/spec.json
