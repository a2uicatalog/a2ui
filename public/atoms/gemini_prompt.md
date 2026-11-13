# Gemini Prompt

Inline Gemini prompt input that calls the GAS callGemini() function from within a rendered page

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (light 360) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (light 360) |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| label | string (optional) |
| placeholder | string (optional) |
| accent | string (optional, hex colour) |

## Example payload

```json
{
  "type": "gemini_prompt"
}
```

Live page: https://a2uicatalog.ai/atoms/gemini_prompt/
Full field contract: https://a2uicatalog.ai/spec.json
