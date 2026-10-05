# Motion Envelope

An envelope that carries a letter. Children are ordinary atoms shown on the letter card. With mode open, the flap flips up and the letter rises out as p goes 0 to 1; with mode seal, the letter drops in, the flap closes and the stamp lands. Optional address line (to) and stamp text. Plain HTML and CSS, no script; standalone it renders the finished state (open: letter out; seal: sealed and stamped). Use inside a motion_timeline to show a message being packed or delivered, e.g. an A2UI payload wrapped as an MCP tool result.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| mode | "open" | "seal" (optional, default "open") |
| width | integer (optional). Envelope width px, 80-900; height is 5/8 of it. Default 360. |
| blocks | array (max 3) of atom blocks shown on the letter. They render finished (they do not follow the envelope's p). |
| to | string (optional, max 60). Address line on the front, e.g. "ui://jobs/board". |
| stamp | string (optional, max 24). Stamp text, e.g. "tool result". In seal mode it lands at the end. |
| label | string (optional, max 40). Accessible name. Default "Envelope". |
| fill | "#rrggbb" (optional). Envelope colour. Default a tint of the stage background. |
| accent | "#rrggbb" (optional). Fold edges and stamp. Default the stage accent. |
| color | "#rrggbb" (optional). Address text. Default the stage ink. |

## Example payload

```json
{
  "type": "motion_envelope",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_envelope/
Full field contract: https://a2uicatalog.ai/spec.json
