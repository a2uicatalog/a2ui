# Motion Code

A code window that types itself in as p goes 0 to 1: monospace lines revealed left to right in order with a caret on the line being typed, keywords in the accent colour and // comments dimmed. No script and no per-letter markup, because a line's width is its character count in ch. For show, not for syntax highlighting. Standalone it renders all the code.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| lines | array (max 14) of string (max 72 characters each). Blank strings are blank lines. |
| file | string (optional, max 32). Shown in the window bar. |
| size | integer (optional). Font size px, 8-60. Default 18. |
| accent | "#rrggbb" (optional). Keywords and caret. Default the stage accent. |

## Example payload

```json
{
  "type": "motion_code",
  "lines": [
    "$ npm install a2ui",
    "added 42 packages",
    "\u2713 Done in 1.2s"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_code/
Full field contract: https://a2uicatalog.ai/spec.json
