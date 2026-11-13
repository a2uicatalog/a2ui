# Collapsible Panel

Renders a standalone section of content that can be toggled between

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| toggle_label | string The text for the control that expands/collapses the content. |
| initial_state | string, default "collapsed" The initial state of the panel ("expanded" or "collapsed"). |
| content | string The main content to be shown or hidden. |

## Example payload

```json
{
  "type": "collapsible_panel",
  "toggle_label": "Toggle label",
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/collapsible_panel/
Full field contract: https://a2uicatalog.ai/spec.json
