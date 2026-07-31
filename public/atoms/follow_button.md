# Follow Button

Displays a single button allowing a user to subscribe directly to a profile.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| target_handle | string. Handle identifier of target profile. |
| platform | string: twitter | github | linkedin. The platform. |

## Example payload

```json
{
  "type": "follow_button",
  "target_handle": "Target handle",
  "platform": "twitter"
}
```

Live page: https://a2uicatalog.ai/atoms/follow_button/
Full field contract: https://a2uicatalog.ai/spec.json
