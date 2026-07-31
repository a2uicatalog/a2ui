# Highlight Box

A visually rich highlighted box with gradient, solid, or outline style. Richer than callout — no severity system, pure design focus.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| text | string (optional, markdown — renderer degrades to empty; provide title and/or text) |
| icon | string (optional, emoji) |
| accent | string (optional, hex, default "#6366f1") |
| style | string (optional, "gradient"|"solid"|"outline", default "gradient") |

## Example payload

```json
{
  "type": "highlight_box"
}
```

Live page: https://a2uicatalog.ai/atoms/highlight_box/
Full field contract: https://a2uicatalog.ai/spec.json
