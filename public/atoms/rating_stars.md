# Rating Stars

A visual component allowing users to rate an item using a series of

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| rating | integer The current rating value (e.g., 3 for 3 stars). |
| max_rating | integer The maximum possible rating (e.g., 5 for 5 stars). |
| is_interactive | boolean Indicates if the stars are clickable for user input. |

## Example payload

```json
{
  "type": "rating_stars",
  "rating": 75,
  "max_rating": 75,
  "is_interactive": true
}
```

Live page: https://a2uicatalog.ai/atoms/rating_stars/
Full field contract: https://a2uicatalog.ai/spec.json
