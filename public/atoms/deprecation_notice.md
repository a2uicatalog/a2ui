# Deprecation Notice

Displays a prominent warning banner indicating a feature or API is no longer supported.

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
| alternative | string. Recommended migration path or replacement feature. |
| removal_version | string. Optional version when the feature will be removed. |

## Example payload

```json
{
  "type": "deprecation_notice",
  "alternative": "new_component"
}
```

Live page: https://a2uicatalog.ai/atoms/deprecation_notice/
Full field contract: https://a2uicatalog.ai/spec.json
