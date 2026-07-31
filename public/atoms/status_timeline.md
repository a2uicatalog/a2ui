# Status Timeline

Vertical timeline with status dots (done/active/pending/error/warning)

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| events | array of {title, date (optional), text (optional), status (done|active|pending|error|warning)} |
| title | string (optional) |

## Example payload

```json
{
  "type": "status_timeline"
}
```

Live page: https://a2uicatalog.ai/atoms/status_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
