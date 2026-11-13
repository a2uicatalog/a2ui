# Flow Connector

Animated dashed beam connecting two labelled nodes — alias for animated_beam. Two shapes — a single from/to/label pair (original), or a multi-node nodes/connectors chain (added 2026-07-24, e.g. an identity/ permission chain of more than 2 hops) where each node can be a bare string (simple pill) or a {role, name, detail} object (richer boxed card).

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
| from | string or {role, name, detail} object (ignored if nodes is set) |
| to | string or {role, name, detail} object (ignored if nodes is set) |
| label | string (optional, ignored if nodes is set) |
| nodes | array (optional). Array of string or {role, name, detail} — 2+ nodes in a single chain, rendered left to right. |
| connectors | array of string (optional). Labels between each consecutive pair in `nodes` — length should be len(nodes)-1. |
| color | string (optional, hex) |
| theme | string (optional, "light"|"dark", default "light") |

## Example payload

```json
{
  "type": "flow_connector",
  "from": "start-node",
  "to": "end-node"
}
```

Live page: https://a2uicatalog.ai/atoms/flow_connector/
Full field contract: https://a2uicatalog.ai/spec.json
