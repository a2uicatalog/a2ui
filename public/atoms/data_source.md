# Data Source

Generic HTTP GET data feed. Fetches on server-side render (GAS surface via UrlFetchApp) then refreshes client-side via google.script.run.fetchDataSource(). Publishes to window.A2UI_DATA[name] and calls window.A2UI_CALLBACKS[name]. Other surfaces would use fetch() or requests instead.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string. Feed identifier — other atoms subscribe to this name (required). |
| url | string. HTTP GET endpoint. |
| format | string (optional). json | text. Default json. |
| path | string (optional). Dot-notation path into parsed response (e.g. data.items). |
| refresh | integer (optional). Client refresh interval seconds. 0 = initial load only. Default 0. |
| cache | integer (optional). Server-side CacheService TTL seconds. Default 15. |

## Example payload

```json
{
  "type": "data_source",
  "name": "Data Source",
  "url": 1
}
```

Live page: https://a2uicatalog.ai/atoms/data_source/
Full field contract: https://a2uicatalog.ai/spec.json
