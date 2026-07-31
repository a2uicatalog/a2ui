# Number Flip

Slot-machine style digit reveal. Each digit flips in from above on load.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | the number or string to display (required) |
| prefix | text before the number |
| suffix | text after the number |
| label | caption below |
| size | font-size CSS value (default 3rem) |
| color | digit colour (default var(--a2ui-accent)) |
| duration | total animation window in ms (default 1200) |
| align | center (default), left |

## Example payload

```json
{
  "type": "number_flip",
  "value": 1,
  "prefix": 1,
  "suffix": 1,
  "label": "Number Flip"
}
```

Live page: https://a2uicatalog.ai/atoms/number_flip/
Full field contract: https://a2uicatalog.ai/spec.json
