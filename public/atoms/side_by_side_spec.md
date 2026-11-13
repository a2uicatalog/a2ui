# Side By Side Spec

Renders a detailed comparison of two items, displaying their attributes

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| item_a_name | string |
| item_b_name | string |
| specs | array |

## Example payload

```json
{
  "type": "side_by_side_spec",
  "item_a_name": "Item a name",
  "item_b_name": "Item b name",
  "specs": [
    {
      "label": "Weight",
      "value": "1.2 kg"
    },
    {
      "label": "Dimensions",
      "value": "20\u00d715 cm"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/side_by_side_spec/
Full field contract: https://a2uicatalog.ai/spec.json
