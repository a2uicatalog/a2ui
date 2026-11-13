# Motion Mark

The catalogue's own mark (three tilted ellipses around a nucleus, one electron) that draws itself as p goes 0 to 1 and whose electron circles its orbit as step goes 0 to 1. The opening frame of a film or a brand sting. Geometry is the site logo's; the two colours are fields. Plain SVG and CSS, no script: it moves with the --p and --s custom properties a motion_timeline p and step track set, and standalone it renders the finished mark.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| size | integer (optional). Width and height px, 24-600. Default 120. |
| accent | "#rrggbb" (optional). Two ellipses and the nucleus. Default the stage accent. |
| accent2 | "#rrggbb" (optional). The third ellipse and the electron. Default "#00b7c3". |

## Example payload

```json
{
  "type": "motion_mark"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_mark/
Full field contract: https://a2uicatalog.ai/spec.json
