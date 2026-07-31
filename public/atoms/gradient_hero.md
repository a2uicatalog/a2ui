# Gradient Hero

Full-width light/pastel gradient hero with badge, large title, subtitle, and optional CTA. Pure CSS — no images. Works on all surfaces. Use when dark_hero is too heavy.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (required, alias heading) |
| subtitle | string (optional, alias subtext) |
| badge | string (optional, label above title) |
| accent | string (optional, hex, default "#6366f1") |
| accent2 | string (optional, second gradient hex, default "#8b5cf6") |
| gradient | string (optional, css gradient override) |
| align | string (optional, "left"|"center", default "left") |
| cta_label | string (optional) |
| cta_url | string (optional) |

## Example payload

```json
{
  "type": "gradient_hero",
  "title": "Gradient Hero"
}
```

Live page: https://a2uicatalog.ai/atoms/gradient_hero/
Full field contract: https://a2uicatalog.ai/spec.json
