# Inline Alert

Compact inline-level alert embedded within content flow — an icon and short message that appears beside labels, form fields, or within paragraphs without disrupting layout. Distinct from alert_banner (full-width strip) and toast_notification (transient overlay).

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
| variant | string. Severity — "info", "success", "warning" or "error". "critical" is accepted as a synonym for "error" (see alert_banner). NOT `type`, which is the block discriminator — a severity put there is ignored or replaces the atom name. Renderers read `variant`. |
| message | string. The alert text. |
| detail | string (optional). A secondary line of smaller detail text. |
| icon | string (optional). Override the default icon for the severity type. |

## Example payload

```json
{
  "type": "inline_alert",
  "variant": "primary",
  "message": "Your action was completed successfully."
}
```

Live page: https://a2uicatalog.ai/atoms/inline_alert/
Full field contract: https://a2uicatalog.ai/spec.json
