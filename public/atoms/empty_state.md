# Empty State

A UI pattern displayed when there is no data to show, often with an image, message, and an optional call to action.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| image_url | string Optional URL for an illustrative image. |
| title | string The main title for the empty state. |
| description | string A descriptive message explaining why the state is empty. |
| action_label | string Optional text for a call to action button. |
| action_url | string Optional URL for the call to action button. |

## Example payload

```json
{
  "type": "empty_state",
  "title": "Empty State",
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/empty_state/
Full field contract: https://a2uicatalog.ai/spec.json
