# Content Tabs

Tabbed panels where each pane holds real nested atom blocks — the generic multi-section single-page container ("several distinct views of one payload") without needing named-page infrastructure. Unlike `tabs` (code-oriented, single content string per pane), each pane runs the shared block renderer over its own blocks array, like color_section/columns do for their children.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Not supported | 2026-11-13 | a nested atom type is unknown |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| accent | string (optional). Active-tab underline colour. |
| default_index | integer (optional, default 0). Which tab is open on load. |
| tabs | [{'label': 'string', 'blocks': 'array of atom blocks', 'max_width': 'string (optional, e.g. "90%" or "800px"). Caps and centres this tab\'s own panel content, independent of any color_section a tab\'s blocks may also use — set uniformly across tabs for a consistent inset regardless of each tab\'s internal wrapping.'}] |

## Example payload

```json
{
  "type": "content_tabs"
}
```

Live page: https://a2uicatalog.ai/atoms/content_tabs/
Full field contract: https://a2uicatalog.ai/spec.json
