# Cta Section

Full-width call-to-action banner with headline, body text, a primary button, and an optional secondary ghost button. Renders on a solid color background. Tailwind UI CTA section pattern.

## Surfaces

web, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| heading | string. Main headline. |
| body | string. Descriptive paragraph. |
| primary_cta | object. {label, url} for the primary action button. |
| secondary_cta | object (optional). {label, url} for a ghost secondary button. |
| background | string (optional). CSS color for the banner background. Default |

## Example payload

```json
{
  "type": "cta_section",
  "heading": "Cta Section",
  "body": "A concise description of the content.",
  "primary_cta": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/cta_section/
Full field contract: https://a2uicatalog.ai/spec.json
