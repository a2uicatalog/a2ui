# Follow Button

Displays a single button allowing a user to subscribe directly to a profile.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
