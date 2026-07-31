# User Profile Card

Personalised profile card showing the active user's avatar initial, display name (derived from email), email address, and Workspace domain. On GAS uses Session.getActiveUser(); on other surfaces renders from name/email fields.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string (static connector). Display name for non-GAS surfaces. |
| email | string (static connector). Email address for non-GAS surfaces. |
| accent | string (optional). Avatar background colour. |
| subtitle | string (optional). Role or team label shown below the email. |

## Example payload

```json
{
  "type": "user_profile_card",
  "name": "User Profile Card",
  "email": "user@example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/user_profile_card/
Full field contract: https://a2uicatalog.ai/spec.json
