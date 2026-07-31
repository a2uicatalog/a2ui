# Back Button

Styled back navigation button. Links to a URL, a named page slug, or browser history. Three visual styles.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional, default "← Back") |
| url | string (optional, href) |
| nav_slug | string (optional, resolves to ?nav=<slug>) |
| style | string (optional, "ghost"|"outline"|"text", default "ghost") |
| accent | string (optional, hex, default "#6366f1") |

## Example payload

```json
{
  "type": "back_button"
}
```

Live page: https://a2uicatalog.ai/atoms/back_button/
Full field contract: https://a2uicatalog.ai/spec.json
