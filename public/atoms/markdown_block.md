# Markdown Block

Renders a Markdown string as formatted inline HTML - bold, italic, inline code and links (http, https, mailto, tel or relative). Block syntax (headings, lists, tables, fenced code) is not rendered. Adapted from the MarkDownRenderer pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
