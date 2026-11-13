# Scroll Trigger

Content that animates in from a direction when scrolled into view — alias for reveal_on_scroll

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| text | string (alias: content) |
| title | string (optional) |
| delay | number (optional, seconds) |
| direction | string (optional, up|down|left|right) |

## Example payload

```json
{
  "type": "scroll_trigger",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/scroll_trigger/
Full field contract: https://a2uicatalog.ai/spec.json
