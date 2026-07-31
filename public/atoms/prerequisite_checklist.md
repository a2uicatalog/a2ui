# Prerequisite Checklist

Renders a callout box highlighting required tools, knowledge, or setups needed before starting a guide.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string. Custom header text for the prerequisite warning block. |
| items | array. Strings containing descriptions of individual setup requirements. |

## Example payload

```json
{
  "type": "prerequisite_checklist",
  "title": "Prerequisite Checklist",
  "items": [
    {
      "label": "First item"
    },
    {
      "label": "Second item"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/prerequisite_checklist/
Full field contract: https://a2uicatalog.ai/spec.json
