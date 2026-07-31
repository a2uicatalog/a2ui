# Orbit Diagram

Animated orbiting node diagram — central node with satellite labels on a dashed orbit ring

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| center | string (label for the central node) |
| nodes | array of strings or {label, color} objects |
| color | string (optional, hex accent) |
| speed | number (optional, animation speed) |

## Example payload

```json
{
  "type": "orbit_diagram",
  "center": "Core Concept",
  "nodes": [
    {
      "id": "node-1",
      "label": "Node 1"
    },
    {
      "id": "node-2",
      "label": "Node 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/orbit_diagram/
Full field contract: https://a2uicatalog.ai/spec.json
