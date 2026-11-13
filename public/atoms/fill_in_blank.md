# Fill In Blank

Cloze-test exercise where one or more blanks in a sentence or paragraph are replaced by inline input fields. On submission a minimal inline script compares trimmed lowercase input against accepted answers and highlights each blank green (correct) or red (wrong). A retry button resets all inputs.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| template | string. Sentence with {blank} placeholders marking each gap. |
| answers | list[string | list[string]]. Accepted answer(s) per blank in order. A list entry may itself be a list of acceptable alternatives. |
| hint | string (optional). Shown below the exercise as a nudge. |
| case_sensitive | boolean (optional, default false). |

## Example payload

```json
{
  "type": "fill_in_blank",
  "template": "Hello, {{name}}!",
  "answers": [
    {
      "text": "Option A"
    },
    {
      "text": "Option B"
    },
    {
      "text": "Option C"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/fill_in_blank/
Full field contract: https://a2uicatalog.ai/spec.json
