# Progress Reveal

Animated progress bar that counts from 0 to a value when scrolled into view

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | number (0–100, alias: percent) |
| label | string (optional, alias: title) |
| color | string (optional, hex) |
| suffix | string (optional, default %) |
| height | number (optional, bar height px) |

## Example payload

```json
{
  "type": "progress_reveal",
  "value": 75
}
```

Live page: https://a2uicatalog.ai/atoms/progress_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
