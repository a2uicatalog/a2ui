# Modal

Modal dialog overlay with a title, configurable size, and arbitrary content children. Opened programmatically or via a trigger button. Closes on X, Escape, or backdrop click.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | contrast worse than React (dark 360); contrast worse than React (dark 480); pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string. Modal heading. |
| size | string (optional). One of: sm, md, lg. Default: md. |
| children | {'type': 'array', 'description': 'Content atoms to render inside the modal body.'} |
| trigger_label | string (optional). If set, renders a button that opens the modal. |

## Example payload

```json
{
  "type": "modal",
  "title": "Modal",
  "children": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/modal/
Full field contract: https://a2uicatalog.ai/spec.json
