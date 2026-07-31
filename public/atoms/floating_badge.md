# Floating Badge

An emoji or icon that bobs up and down continuously. Great for CTAs and achievement moments.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| icon | emoji or character to float (required) |
| label | optional caption below |
| size | sm, md (default), lg |
| speed | bob cycle in seconds (default 3) |
| shadow | drop shadow that deepens on rise (default true) |
| align | center (default), left, right |

## Example payload

```json
{
  "type": "floating_badge",
  "icon": "\u2b50"
}
```

Live page: https://a2uicatalog.ai/atoms/floating_badge/
Full field contract: https://a2uicatalog.ai/spec.json
