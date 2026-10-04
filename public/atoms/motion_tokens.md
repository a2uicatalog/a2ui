# Motion Tokens

The catalogue's motion vocabulary, drawn: every named easing curve with a dot riding it, the cubic-bezier it stands for and what it is for, the five duration tokens, and the nine entrance effects. The same names are accepted by the `enter` prop on any atom, by motion_group, by reveal, and by every ease field in motion_timeline, so an agent learns the vocabulary once. Honours prefers-reduced-motion (dots stay still).

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| show | "ease" | "duration" | "both" (optional, default "both") |
| theme | "dark" | "light"  (optional, default "dark") |
| accent | "#rrggbb" (optional). Default "#38bdf8". |

## Example payload

```json
{
  "type": "motion_tokens"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_tokens/
Full field contract: https://a2uicatalog.ai/spec.json
