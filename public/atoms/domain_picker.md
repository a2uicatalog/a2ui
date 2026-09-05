# Domain Picker

One filled pill ("use my saved default") beside a free-text field, for a config question that almost always wants the same answer but sometimes needs a one-off override. The pill and the field write the SAME target ValueStore — whichever the reader touched last wins, so there is no separate "which mode" flag anywhere to fall out of sync.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| target | string (required). A ValueStore primitive's id. |
| default_option | object {label} (optional). The pill's label, e.g. "From my profile". |
| default_domains | string (optional). What the pill resets target to. |
| free_entry | object {placeholder} (optional). Placeholder for the text field. |

## Example payload

```json
{
  "type": "domain_picker",
  "target": "end-node"
}
```

Live page: https://a2uicatalog.ai/atoms/domain_picker/
Full field contract: https://a2uicatalog.ai/spec.json
