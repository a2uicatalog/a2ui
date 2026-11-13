# User Profile Card

Personalised profile card showing the active user's avatar initial, display name (derived from email), email address, and Workspace domain. On GAS uses Session.getActiveUser(); on other surfaces renders from name/email fields.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
