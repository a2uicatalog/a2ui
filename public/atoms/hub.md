# Hub

Full-screen deck navigation container: subjects as a coloured nav rail, each holding slides of atom blocks. The envelope for hub/deck payloads.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| subjects | array (required) of {id, label, color (hex), slides: [{id, label, blocks: [atom blocks]}]} |
| background | string (optional, page hex, default "#0f172a") |
| nav_background | string (optional, nav rail hex, defaults to background) |

## Example payload

```json
{
  "type": "hub",
  "subjects": []
}
```

Live page: https://a2uicatalog.ai/atoms/hub/
Full field contract: https://a2uicatalog.ai/spec.json
