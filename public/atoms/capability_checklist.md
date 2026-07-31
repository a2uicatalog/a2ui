# Capability Checklist

Renders a list of capabilities, indicating which items possess each

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| capability_names | array |
| items | array |

## Example payload

```json
{
  "type": "capability_checklist",
  "capability_names": [
    "Vision",
    "Code execution",
    "Web search"
  ],
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

Live page: https://a2uicatalog.ai/atoms/capability_checklist/
Full field contract: https://a2uicatalog.ai/spec.json
