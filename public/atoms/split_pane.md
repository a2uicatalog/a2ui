# Split Pane

Two-panel split layout with distinct background colors per pane. Each pane renders atom blocks independently. Unlike columns, each side has its own background.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| left | object — {bg (css color, default "#f8fafc"), blocks (atom blocks)} |
| right | object — {bg (css color, default "#fff"), blocks (atom blocks)} |

## Example payload

```json
{
  "type": "split_pane"
}
```

Live page: https://a2uicatalog.ai/atoms/split_pane/
Full field contract: https://a2uicatalog.ai/spec.json
