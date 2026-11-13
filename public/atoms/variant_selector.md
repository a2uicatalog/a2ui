# Variant Selector

CSS-only variant picker — each option is a selectable card with a label and optional description, rendered as hidden radio inputs with label:has(input:checked) styling. Used for product size, colour, or plan variant selection. Adapted from the RadioGroup/RadioItem pattern in OpenUI OUI benchmark samples.

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
| name | string. Form field name used in radio input group. |
| label | string (optional). Group label shown above the options. |
| items | {'type': 'array', 'description': 'List of {value, title, description?} option objects.'} |
| default_value | string (optional). Pre-selected option value. |

## Example payload

```json
{
  "type": "variant_selector",
  "name": "Variant Selector",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/variant_selector/
Full field contract: https://a2uicatalog.ai/spec.json
