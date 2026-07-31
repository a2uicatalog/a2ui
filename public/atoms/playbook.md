# Playbook

Full-screen multi-slide presentation deck — each slide is its own atom block array, with shared data feeds and slide navigation

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| slides | array of {id (optional), blocks: [atom block objects]} — each slide is a full block list |
| shared_blocks | array of atom block objects with role:data_source (optional). Rendered once before slides. Use for adsb_feed, metar_feed, firestore_read etc. — atoms that publish to window.A2UI_CALLBACKS[name] and have no visual output. Visual atoms in slides bind by name via data_source / weather_source / connector fields. |
| transition | string (optional, fade|slide, default fade) |

## Example payload

```json
{
  "type": "playbook"
}
```

Live page: https://a2uicatalog.ai/atoms/playbook/
Full field contract: https://a2uicatalog.ai/spec.json
