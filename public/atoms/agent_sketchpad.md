# Agent Sketchpad

A single composite SVG canvas built from an ORDERED list of validated SVG elements, for an agent to progressively draw one coherent picture across multiple real updates (e.g. one A2A message per shape) rather than svg_path_draw's one-shot single shape. Every re-render draws all elements except the last as already-complete (no animation); only the LAST element in the list gets the real stroke-dasharray/stroke-dashoffset draw-in animation -- a stateless rule that works under this catalogue's full-rerender model without any incremental DOM patching. Redesigned 2026-08-24 from a path-only shape to a general SVG-primitive one (with fill), to match what a real freeform tool-calling loop actually produces (see streaming-testbench's demos/sketch/sketch_agent.py, the origin of this atom's validation approach) -- works anywhere svg_path_draw does.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| strokes | array of {element, label?} (required). ORDERED -- element is RAW SVG MARKUP for exactly ONE element (real creative freedom within a fixed safety allowlist, not a raw pass-through): one of circle, ellipse, rect, line, polyline, polygon, path, g (g may nest further allowed elements). Allowed attributes: cx, cy, r, rx, ry, x, y, width, height, x1, y1, x2, y2, points, d, fill, stroke, stroke-width, opacity, fill-opacity, stroke-opacity, stroke-linecap, stroke-linejoin, transform -- attribute values are restricted to a safe alphanumeric/punctuation character class (blocks javascript:, event handlers, anything script-shaped). The renderer parses and re-validates every element server-side before embedding it (never trusts the string as-is) -- an element that fails validation (disallowed tag/attribute, unsafe value, malformed markup, more than one top-level element) is skipped with a console warning, not a crash. label is an optional short phrase describing that one element (e.g. "the lighthouse tower"), not rendered, useful for an agent-facing tool-call log. Resend the FULL, growing array on every update (A2UI messages carry full values, not deltas) -- only the LAST item in the array animates; everything before it renders as already-drawn. Capped defensively at 250 elements and 4096 raw markup characters per element by the renderer (over-cap elements are skipped with a console warning, not a crash). |
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
