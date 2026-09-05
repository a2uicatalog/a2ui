# Lens Grid

Grid of selectable cards for a config question with a small fixed set of options, each worth a short explanation — unlike a dropdown, which hides the explanation until opened. Not driven by the standard onClick wire (there is no event carrying "which card"); pass target (a ValueStore id) and the card's own click updates it directly, mirroring theme_toggle's persist_to pattern.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| target | string (required). A ValueStore primitive's id, set to a card's value on click. |
| options | array of {value, label, caption?, selected?} (required). |
| columns | number (optional, default 2). |
| gap | number (optional, px, default 10). |
| selected | string (optional). Current value, for which card renders highlighted on first paint — a repaint must pass the reader's last choice back in here or it resets, same rule as theme_toggle's initial. |

## Example payload

```json
{
  "type": "lens_grid",
  "target": "end-node",
  "options": [
    {
      "label": "Option A",
      "value": "a"
    },
    {
      "label": "Option B",
      "value": "b"
    },
    {
      "label": "Option C",
      "value": "c"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/lens_grid/
Full field contract: https://a2uicatalog.ai/spec.json
