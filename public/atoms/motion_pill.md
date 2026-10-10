# Motion Pill

A rounded call-to-action chip: "Comment *Motion* under this post". The words between asterisks take the accent colour (two asterisks in a row are a literal one), with an optional leading glyph. It fades and rises with p, and put in a layer with layer:"hud" it stays on screen across every scene and camera move, the way social films keep their ask visible. Plain HTML and CSS, no script: it moves with the --p custom property a motion_timeline p track sets, and standalone it renders its final state.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| text | string (max 60). Default "Label". *word* takes the accent colour; ** is a literal asterisk. |
| icon | string (optional, max 2). A glyph before the text, in the accent colour. |
| size | integer (optional). Font size px, 10-120. Default 28. |
| accent | "#rrggbb" (optional). Default the stage accent. |
| color | "#rrggbb" (optional). Text colour. Default the stage ink. |
| fill | "#rrggbb" (optional). Chip fill. Default a faint tint of the stage ink. |
| border_gradient | ["#rrggbb", "#rrggbb"] (optional). A two-colour gradient outline instead of the faint line. |
| glow | integer (optional). A soft glow around the chip, 0-40 px, in the gradient colours or the accent. Default 0 (off). |
| href | string (optional). Makes the pill a real link: https, mailto or a relative path; anything else is dropped. Default none. |
| align | "start" | "middle" | "end" (optional, default "start") |

## Example payload

```json
{
  "type": "motion_pill"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_pill/
Full field contract: https://a2uicatalog.ai/spec.json
