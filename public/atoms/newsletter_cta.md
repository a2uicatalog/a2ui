# Newsletter Cta

Displays an input block encouraging readers to subscribe to an email update list.

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
| headline | string. Header message prompting subscription. |
| button_label | string. Optional submit button text, defaults to Subscribe. |

## Example payload

```json
{
  "type": "newsletter_cta",
  "headline": "Main headline text here"
}
```

Live page: https://a2uicatalog.ai/atoms/newsletter_cta/
Full field contract: https://a2uicatalog.ai/spec.json
