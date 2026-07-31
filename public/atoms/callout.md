# Callout

Highlighted alert box — info, warning, tip, or danger

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| kind | info | warning | tip | danger |
| title | string (optional) |
| text | string |

## Example payload

```json
{
  "type": "callout",
  "kind": "info",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/callout/
Full field contract: https://a2uicatalog.ai/spec.json
