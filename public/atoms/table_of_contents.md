# Table Of Contents

Renders an active list directory of navigation links targeting main content sections.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| headings | array. Structured items detailing section names and anchor tags. |

## Example payload

```json
{
  "type": "table_of_contents",
  "headings": [
    {
      "level": 2,
      "text": "Introduction"
    },
    {
      "level": 2,
      "text": "Methods"
    },
    {
      "level": 2,
      "text": "Results"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/table_of_contents/
Full field contract: https://a2uicatalog.ai/spec.json
