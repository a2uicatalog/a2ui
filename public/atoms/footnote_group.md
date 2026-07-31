# Footnote Group

Renders a numbered list of footnotes at the bottom of an article or section.

## Surfaces

web, email, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| footnotes | array of {id, text}. Footnote entries. |

## Example payload

```json
{
  "type": "footnote_group",
  "footnotes": [
    {
      "id": 1,
      "text": "Source: Example Report, 2026."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/footnote_group/
Full field contract: https://a2uicatalog.ai/spec.json
