# Form Switch Group

Group of named toggle switches — on/off controls with optional labels and descriptions. Suitable for settings panels, notification preferences, and feature flags.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| label | string (optional). Section label above the switches. |
| name | string. Aggregate field identifier. |
| items | {'type': 'array', 'description': 'List of {name, label?, description?, default_checked?} entries.'} |

## Example payload

```json
{
  "type": "form_switch_group",
  "name": "Form Switch Group"
}
```

Live page: https://a2uicatalog.ai/atoms/form_switch_group/
Full field contract: https://a2uicatalog.ai/spec.json
