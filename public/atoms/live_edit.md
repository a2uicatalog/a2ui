# Live Edit

Embedded mini schema editor with a textarea for typing a single atom JSON block and a live rendered preview below

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| placeholder | string (optional, example atom JSON) |
| accent | string (optional, hex) |
| renderer_url | string (optional, renderer base URL for linking) |

## Example payload

```json
{
  "type": "live_edit"
}
```

Live page: https://a2uicatalog.ai/atoms/live_edit/
Full field contract: https://a2uicatalog.ai/spec.json
