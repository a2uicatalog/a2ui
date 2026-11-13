# Alert Banner

A prominent banner displaying a message, often with an icon and an optional action.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| text | string. The banner message. NOT `message` — every renderer reads `text`, so a banner built with `message` renders empty apart from its icon. |
| variant | string. Severity — "info", "success", "warning" or "critical". "error" is accepted as a synonym for "critical": inline_alert knows the first word and this atom the second, and each used to fall back silently to "info" on the other. NOT `type`, which is the block discriminator. |
| icon | string Optional icon name to display next to the message. |
| action_label | string Optional text for an action button. |
| action_url | string Optional URL for the action button. |

## Example payload

```json
{
  "type": "alert_banner",
  "text": "A concise description of the content.",
  "variant": "primary"
}
```

Live page: https://a2uicatalog.ai/atoms/alert_banner/
Full field contract: https://a2uicatalog.ai/spec.json
