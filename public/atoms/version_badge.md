# Version Badge

Displays a small visual tag showing software release or dependency version numbers.

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
| version | string. The semantic version number or release label to display. |
| status | string: stable | beta | alpha | rc. The lifecycle stage. |

## Example payload

```json
{
  "type": "version_badge",
  "version": 1,
  "status": "Active"
}
```

Live page: https://a2uicatalog.ai/atoms/version_badge/
Full field contract: https://a2uicatalog.ai/spec.json
