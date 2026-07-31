# Numbered List

Numbered list with large decorative number backgrounds ("large" style), circular number badges ("badge" style), or bordered cards with a ghost-number, title, tag pills and body text ("cards" style, added 2026-07-24 for stage-by-stage architecture breakdowns). More visual than steps.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Ignored by the "cards" style. |
| accent | string (optional, hex, default "#6366f1") |
| theme | string (optional, "light"|"dark", default "light"). "cards" style only. |
| style | string (optional, "large"|"badge"|"cards", default "large") |
| items | array (required). For "large"/"badge" style, each item is {label (optional), text (optional)}. For "cards" style, each item is {number (optional, defaults to position), title, tags (optional, array of string), text}. |

## Example payload

```json
{
  "type": "numbered_list"
}
```

Live page: https://a2uicatalog.ai/atoms/numbered_list/
Full field contract: https://a2uicatalog.ai/spec.json
