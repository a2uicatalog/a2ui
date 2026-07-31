# Match Exercise

Click-to-pair matching exercise. Two columns of items are shown — left (terms) and right (definitions). Learner clicks a term then a definition to form a pair. Matched pairs lock and highlight green; a mismatch briefly flashes red then resets. A score chip shows pairs matched / total. Driven by a minimal inline script.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| pairs | list[{term: string, definition: string}]. 3 to 8 pairs recommended. |
| shuffle | boolean (optional, default true). Randomise right-column order on render. |

## Example payload

```json
{
  "type": "match_exercise",
  "pairs": [
    {
      "key": "API_KEY",
      "value": "your-key"
    },
    {
      "key": "ENV",
      "value": "production"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/match_exercise/
Full field contract: https://a2uicatalog.ai/spec.json
