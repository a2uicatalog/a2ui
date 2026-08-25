# Freeform Escape-Hatch Atom — Architectural Exploration & Proposal

**Status:** Proposed / Exploration  
**Area:** Schema & Atom Taxonomy (`atoms/schema.yaml`, `renderers/`, `cloud-run-renderer/`)

---

## Executive Summary

This proposal evaluates whether the validated SVG primitive pattern used in `agent_sketchpad` (`circle`, `ellipse`, `rect`, `line`, `polyline`, `polygon`, `path`, `g`) generalizes into a universal **expression fallback atom** across the A2UI ecosystem (~550 atoms).

In the rendering pipeline, `cloud-run-renderer` (headless Chromium) provides a universal **render fallback** at late stages by rasterizing complex atoms into flat images for constrained surfaces like Google Chat. This exploration asks whether an equivalent universal **expression fallback** belongs earlier in the pipeline—allowing an authoring agent to emit arbitrary visual structures when no catalog atom matches.

---

## The Core Tension

### The Promise: Expressive Resilience
In an open-ended catalog of ~550 atoms, generative agents occasionally encounter niche domain representations (e.g., unique topological graphs, circuit diagrams, geometric proofs, specialized engineering sketches) that no standard atom captures. A safe freeform canvas gives the agent an expressive safety valve without breaking JSON-schema validation or stalling.

### The Pitfall: Design-System Collapse & The Lazy Agent Anti-Pattern
Every design system with a generic "custom content" or "freeform" escape hatch risks hitting the **path of least resistance**:
1. **Agent Defaulting:** LLMs under token or reasoning pressure gravitate toward unconstrained escape hatches instead of retrieving the most semantically precise atom from the catalog.
2. **Cross-Surface Fragility:** Unstructured visual trees do not adapt across target surfaces (Google Chat cards, Google Meet stage, Apps Script side panels, CLI, or Email). Chat cards require strict widget constraints (`textParagraph`, `decoratedText`, `buttonList`); raw freeform must degrade to headless rasterization every time.
3. **Accessibility Black Hole:** Arbitrary vector geometries lack semantic DOM roles, interactive focus order, and screen-reader hierarchy unless explicitly forced by schema contracts.
4. **State & Mutation Blindness:** A2UI v1.0 data binding and state updates (`updateDataModel`, `ChildList`, ComponentId addressing) operate cleanly on typed fields (`items`, `value`, `metrics`), but cannot predictably mutate or inspect unstructured SVG trees.

---

## Architectural Findings & Verdict

### Recommendation: Do NOT Build a Generic "Anything Else" UI Atom; Scope Strictly to Diagrammatic Vectors

A general-purpose "custom HTML/UI" atom must **NOT** be added. However, a structured **vector diagramming / canvas primitive** (`freeform_canvas` or graduated `agent_sketchpad`) is viable **only** under strict boundary invariants:

1. **Strict Vector Containment:** No arbitrary DOM, no CSS class overrides, no `<foreignObject>`, no inline `<script>`, and no external URL loading (`<image xlink:href="...">`).
2. **Mandatory Semantic & Text Fallback:** Schema must enforce `summary` and `aria_label` fields to provide a first-class text-only degradation for Google Chat, email, and accessibility tooling.
3. **Prompt Friction & Intent Routing:** The agent system prompt and catalog index must position the atom exclusively as a *diagrammatic illustration canvas*, forbidding its use for layouts, forms, stats, or text lists.

---

## Proposed Schema Specification: `freeform_canvas`

If implemented in a future milestone, the schema should adhere to the following declarative specification:

### YAML Schema Definition
```yaml
- type: freeform_canvas
  stage: preview
  description: >
    A bounded, declarative SVG vector canvas for domain-specific diagrams,
    topological graphs, and geometric illustrations where no specialized atom exists.
    Enforces a strict element allowlist with normalized viewBox coordinates and
    mandatory accessibility fallback.
  compact_description: safe declarative SVG vector canvas for custom diagrams
  surfaces:
    works_on:
      - web
      - google-apps-script-web
      - mcp-apps
    degraded_on:
      - surface: google-chat
        note: Degrades to text summary or signed Chromium-rendered PNG
      - surface: google-meet-stage
        note: Renders statically without vector animations
      - surface: email
        note: Renders summary text and static raster fallback
  fields:
    summary: string (required). Plain-text descriptive summary of the visual content, used for accessibility and text-only surfaces.
    viewbox: string (optional, default "0 0 800 500"). Coordinate boundary for responsive scaling.
    background: string (optional). Canvas background fill (hex or CSS color token).
    elements: >
      array of objects (required). Ordered list of validated SVG primitives:
      rect, circle, ellipse, line, polyline, polygon, path, g, text.
      Each element supports an allowlisted set of attributes:
      x, y, x1, y1, x2, y2, cx, cy, r, rx, ry, d, points,
      fill, stroke, stroke_width, stroke_dasharray, opacity, transform,
      font_size, font_weight, font_family, text_anchor.
  source:
    name: a2uicatalog
    url: https://github.com/a2uicatalog/a2ui
    license: MIT
```

### Example Valid Payload
```json
{
  "type": "freeform_canvas",
  "summary": "Three-node ring topology diagram with data flow directional indicators.",
  "viewbox": "0 0 600 300",
  "background": "#0f172a",
  "elements": [
    {
      "tag": "rect",
      "x": 20,
      "y": 20,
      "width": 560,
      "height": 260,
      "rx": 12,
      "fill": "#1e293b",
      "stroke": "#334155",
      "stroke_width": 1
    },
    {
      "tag": "circle",
      "cx": 150,
      "cy": 150,
      "r": 40,
      "fill": "#0284c7",
      "stroke": "#38bdf8",
      "stroke_width": 2
    },
    {
      "tag": "circle",
      "cx": 450,
      "cy": 150,
      "r": 40,
      "fill": "#0284c7",
      "stroke": "#38bdf8",
      "stroke_width": 2
    },
    {
      "tag": "path",
      "d": "M 190 150 L 410 150",
      "stroke": "#94a3b8",
      "stroke_width": 2,
      "stroke_dasharray": "6 4"
    },
    {
      "tag": "text",
      "x": 150,
      "y": 155,
      "fill": "#ffffff",
      "font_size": 14,
      "text_anchor": "middle",
      "font_weight": "bold",
      "text": "Node A"
    },
    {
      "tag": "text",
      "x": 450,
      "y": 155,
      "fill": "#ffffff",
      "font_size": 14,
      "text_anchor": "middle",
      "font_weight": "bold",
      "text": "Node B"
    }
  ]
}
```

---

## Next Steps for Future Implementation
1. **Catalog Decision:** Keep `agent_sketchpad` focused on live agent run visualization; do not overload it with arbitrary layout duty.
2. **Follow-up PR:** If `freeform_canvas` is adopted, introduce `renderers/web_article.py` and Apps Script / GAS mirrors with rigorous attribute sanitization before promoting past `stage: preview`.
