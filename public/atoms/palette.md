# Palette

Sets page-level CSS custom properties (accent colours, block gap) for consistent theming across all atoms. Use as the first block in any payload.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| accent | hex colour string. Sets --a2ui-accent CSS var used by all atoms as default accent. |
| accent2 | hex colour string (optional). Secondary accent. |
| block_gap | CSS length (default 1.25rem). Vertical gap between atom blocks. |
| text_color | hex (optional). Overrides --text CSS var. |
| bg_color | hex (optional). Overrides --bg CSS var. |

## Example payload

```json
{
  "type": "palette"
}
```

Live page: https://a2uicatalog.ai/atoms/palette/
Full field contract: https://a2uicatalog.ai/spec.json
