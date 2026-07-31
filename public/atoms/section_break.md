# Section Break

Labeled or plain section divider. Supports solid, dashed, or dotted line styles. With a label, renders text centered in the line (Notion-style).

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional, centered in divider line) |
| style | string (optional, "line"|"dashed"|"dots", default "line") |
| accent | string (optional, hex line color, default "#e5e7eb") |

## Example payload

```json
{
  "type": "section_break"
}
```

Live page: https://a2uicatalog.ai/atoms/section_break/
Full field contract: https://a2uicatalog.ai/spec.json
