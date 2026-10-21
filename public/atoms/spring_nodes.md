# Spring Nodes

Mass-spring graph: nodes repel each other (Coulomb) and are held by Hooke springs on defined edges. By default a settled, static layout computed server-side, so it works everywhere, including print and assistive tech. Drag-to-pin with live springs is opt-in with interactive: true.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| nodes | array (optional). Array of {id, label} objects. Defaults to 6 labelled nodes. |
| edges | array (optional). Array of {a, b} index pairs for spring connections. |
| colour | string (optional). Node and edge accent colour. Default |
| bg | string (optional). Background colour. Default |
| height | integer (optional). Canvas height px. Default 420. |
| rest_length | integer (optional). Spring rest length px. Default 110. |
| interactive | boolean (optional). Default false: a settled, static layout that works everywhere and for assistive tech. Set true when the atom is shown in a live browser or app view and the viewer should be able to play with the graph: drag nodes to pin them, watch the springs react. Ignored under reduced motion and on static surfaces (print, slides, email, chat, and any surface that strips scripts). |

## Example payload

```json
{
  "type": "spring_nodes"
}
```

Live page: https://a2uicatalog.ai/atoms/spring_nodes/
Full field contract: https://a2uicatalog.ai/spec.json
