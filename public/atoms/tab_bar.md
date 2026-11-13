# Tab Bar

A horizontal navigation component displaying a set of clickable tabs.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| tabs | list of {label: string, url: string, is_active: boolean, icon: string (optional, e.g., 'home')} |

## Example payload

```json
{
  "type": "tab_bar"
}
```

Live page: https://a2uicatalog.ai/atoms/tab_bar/
Full field contract: https://a2uicatalog.ai/spec.json
