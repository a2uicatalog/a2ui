# Agent Sketchpad

A single composite SVG canvas built from an ORDERED list of path strokes, for an agent to progressively draw one coherent picture across multiple real updates (e.g. one A2A message per stroke) rather than svg_path_draw's one-shot single shape. Every re-render draws all strokes except the last as already-complete (no animation); only the LAST stroke in the list gets the real stroke-dasharray/stroke-dashoffset draw-in animation -- a stateless rule that works under this catalogue's full-rerender model without any incremental DOM patching. Designed 2026-08-24 for real streaming multi-step drawing over A2A (see a2a_counterpart/agui_adapter.py); works anywhere svg_path_draw does.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| strokes | array of {path, color?, width?} (required). ORDERED -- path is a raw SVG path "d" string (real creative freedom, not a fixed shape enum). color/width optional per-stroke, default "currentColor"/2. Resend the FULL, growing array on every update (A2UI messages carry full values, not deltas) -- only the LAST item in the array animates; everything before it renders as already-drawn. Capped defensively at 250 strokes and 4096 chars per path by the renderer (malformed/ oversized path data is skipped with a console warning, not a crash). |
| viewBox | string (optional). SVG viewBox, e.g. "0 0 400 200". Default "0 0 400 200" -- pick a canvas shape that fits what's being drawn, unlike svg_path_draw's fixed 400x80 box. |
| label | string (optional). Caption below the canvas. |

## Example payload

```json
{
  "type": "agent_sketchpad"
}
```

Live page: https://a2uicatalog.ai/atoms/agent_sketchpad/
Full field contract: https://a2uicatalog.ai/spec.json
