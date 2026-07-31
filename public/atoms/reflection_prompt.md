# Reflection Prompt

Structured free-text reflection textarea with a submit button. Saves the response to progress_store under the key "reflect:<prompt_id>". On GAS this persists to the learner's progress Sheet. Restores previously saved text on revisit.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| prompt | string (required). The reflection question shown above the textarea. |
| prompt_id | string (optional). Key suffix for progress_store. Default "reflection". |
| placeholder | string (optional). Textarea placeholder text. |
| accent | string (optional). Accent colour. Default |

## Example payload

```json
{
  "type": "reflection_prompt",
  "prompt": "Describe what you'd like to create."
}
```

Live page: https://a2uicatalog.ai/atoms/reflection_prompt/
Full field contract: https://a2uicatalog.ai/spec.json
