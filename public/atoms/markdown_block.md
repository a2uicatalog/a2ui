# Markdown Block

Renders an arbitrary GitHub-Flavoured Markdown string as formatted HTML — bold, italic, inline code, fenced code blocks, lists, tables, blockquotes, and links. Useful when content is authored in or retrieved as Markdown and needs faithful rendering without mapping to individual atoms. Adapted from the MarkDownRenderer pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

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
