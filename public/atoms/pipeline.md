# Pipeline

Inline left-to-right flow (e.g. build pipeline steps)

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| steps | list[string] |

## Example payload

```json
{
  "type": "pipeline",
  "steps": [
    {
      "title": "Step one",
      "body": "First thing to do."
    },
    {
      "title": "Step two",
      "body": "Then this."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/pipeline/
Full field contract: https://a2uicatalog.ai/spec.json
