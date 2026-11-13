# Orbit Diagram

Animated orbiting node diagram — central node with satellite labels on a dashed orbit ring

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
