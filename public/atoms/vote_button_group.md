# Vote Button Group

Styled multi-option vote selector with three visual variants — pill (rounded filled), neon (dark with cyan glow), and default (flat bordered). Encodes the Cyberpunk Maverick voting pattern as a schema atom. CSS-only interactivity using checkbox/radio inputs.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| options | array of objects — label (string), value (string), selected (boolean optional). |
| style | string (optional). One of pill, neon, default. Default pill. |
| title | string (optional). Section heading above the buttons. |
| allow_multi | boolean (optional). Allow multiple selections. Default false. |

## Example payload

```json
{
  "type": "vote_button_group"
}
```

Live page: https://a2uicatalog.ai/atoms/vote_button_group/
Full field contract: https://a2uicatalog.ai/spec.json
