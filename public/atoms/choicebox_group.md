# Choicebox Group

Card-style option selector where each option renders as a full card with icon, title, and description. The entire card is the click target — richer than radio buttons. Inspired by Vercel Geist Choicebox. Ideal for plan selection, framework choice, and AI-generated setup wizards.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Group heading above the cards. |
| name | string. Form field name for the selected value(s). |
| multiple | boolean (optional, default false). If true allows multiple selections. |
| accent | string (optional, default |
| submit_label | string (optional). If set, renders a submit button below the cards. |
| items | {'type': 'array', 'description': 'List of {value, title, description?, icon?, disabled?} entries.'} |

## Example payload

```json
{
  "type": "choicebox_group",
  "name": "Choicebox Group",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/choicebox_group/
Full field contract: https://a2uicatalog.ai/spec.json
