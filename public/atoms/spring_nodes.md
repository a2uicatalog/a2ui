# Spring Nodes

Interactive mass-spring physics simulation — nodes repel each other (Coulomb) and are held by Hooke springs on defined edges. Click and drag to pin and move nodes. Settles naturally from a stacked initial position.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| nodes | array (optional). Array of {id, label} objects. Defaults to 6 labelled nodes. |
| edges | array (optional). Array of {a, b} index pairs for spring connections. |
| colour | string (optional). Node and edge accent colour. Default |
| bg | string (optional). Background colour. Default |
| height | integer (optional). Canvas height px. Default 420. |
| rest_length | integer (optional). Spring rest length px. Default 110. |

## Example payload

```json
{
  "type": "spring_nodes"
}
```

Live page: https://a2uicatalog.ai/atoms/spring_nodes/
Full field contract: https://a2uicatalog.ai/spec.json
