# Split Pane

Two-panel split layout with distinct background colors per pane. Each pane renders atom blocks independently. Unlike columns, each side has its own background.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
