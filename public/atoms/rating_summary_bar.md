# Rating Summary Bar

Aggregate star-rating histogram showing the percentage breakdown per star level (5★ through 1★). Distinct from rating_stars which shows a single score — this shows the full distribution with bar lengths proportional to vote share.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| average | number. Overall average rating (e.g. 4.3). |
| total | number. Total number of ratings. |
| breakdown | {'type': 'array', 'description': 'List of {stars, count} from 5 down to 1.'} |
| accent | string (optional, default |

## Example payload

```json
{
  "type": "rating_summary_bar",
  "average": 75,
  "total": 5,
  "breakdown": [
    {
      "stars": 5,
      "count": 48
    },
    {
      "stars": 4,
      "count": 30
    },
    {
      "stars": 3,
      "count": 12
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/rating_summary_bar/
Full field contract: https://a2uicatalog.ai/spec.json
