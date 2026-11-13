# Palette

Sets page-level CSS custom properties (accent colours, block gap) for consistent theming across all atoms. Use as the first block in any payload.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
