# Form Checkbox Group

Labelled group of checkboxes for multi-option selection. Each checkbox has a name, visible label, optional description, and optional default checked state.

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
| label | string (optional). Group label. |
| name | string. Aggregate field identifier for form submission. |
| items | {'type': 'array', 'description': 'List of {name, label, description?, default_checked?} entries.'} |
| rules | array of strings (optional). |

## Example payload

```json
{
  "type": "form_checkbox_group",
  "name": "Form Checkbox Group"
}
```

Live page: https://a2uicatalog.ai/atoms/form_checkbox_group/
Full field contract: https://a2uicatalog.ai/spec.json
