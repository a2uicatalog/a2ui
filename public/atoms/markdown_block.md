# Markdown Block

Renders a Markdown string as formatted inline HTML - bold, italic, inline code and links (http, https, mailto, tel or relative). Block syntax (headings, lists, tables, fenced code) is not rendered. Adapted from the MarkDownRenderer pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| content | string. The Markdown source string to render. |
| variant | string (optional). "default" (standard margins) or "compact" (tight spacing for dense layouts). Default is "default". |

## Example payload

```json
{
  "type": "markdown_block",
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/markdown_block/
Full field contract: https://a2uicatalog.ai/spec.json
