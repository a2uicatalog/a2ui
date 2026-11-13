# Breadcrumb

A navigation aid indicating the user's current location within a hierarchical

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
| items | list of {label: string, url: string, is_current: boolean} |

## Example payload

```json
{
  "type": "breadcrumb",
  "items": true
}
```

Live page: https://a2uicatalog.ai/atoms/breadcrumb/
Full field contract: https://a2uicatalog.ai/spec.json
