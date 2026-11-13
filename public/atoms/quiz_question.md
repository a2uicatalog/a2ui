# Quiz Question

Multiple-choice or true/false question card with CSS checkbox trick for answer reveal. Correct option is highlighted green on selection, wrong options dim. No JavaScript required — pure CSS :checked selectors drive the feedback state. Optionally shows an explanation block after any answer is chosen.

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
| question | string. The question text. |
| options | list[string]. Answer options — 2 to 6 items. |
| correct | integer. Zero-based index of the correct option. |
| explanation | string (optional). Shown after any option is selected. |
| style | "default" | "dark" | "minimal"  (optional, default "default") |

## Example payload

```json
{
  "type": "quiz_question",
  "question": "Which option do you prefer?",
  "options": [
    {
      "label": "Option A",
      "value": "a"
    },
    {
      "label": "Option B",
      "value": "b"
    },
    {
      "label": "Option C",
      "value": "c"
    }
  ],
  "correct": 1
}
```

Live page: https://a2uicatalog.ai/atoms/quiz_question/
Full field contract: https://a2uicatalog.ai/spec.json
