# Design Proposal: Freeform Escape-Hatch Atom & Universal Expression Fallback

## Status: Evaluated / Proposed Architecture
**Author**: AI Design Exploration Agent  
**Date**: 2026-08-25  
**Topic**: Universal Expression Fallback vs Structured Catalogue Integrity

---

## Executive Summary

This design document evaluates whether the validated-freeform pattern established by `agent_sketchpad` and `freeform_canvas` can and should generalize into a universal "anything else" expression fallback atom across the A2UI catalogue.

The core finding is that **a generic, unconstrained "anything else" UI/HTML fallback atom should NOT be built**. Universal fallbacks are vital in multi-surface rendering pipelines, but they belong strictly at the **render layer** (e.g. `cloud-run-renderer`'s headless-Chromium rasterization engine), not at the **expression layer**. Introducing an unconstrained expression fallback creates a severe "path of least resistance" failure mode that degrades model steering, breaks cross-surface portability, destroys downstream semantic reasoning in multi-agent workflows, and introduces unmanageable HTML/CSS security vectors.

If future compound layout authoring is required, it must be addressed via a strictly typed, schema-validated **`declarative_layout` (or `composite_container`) atom** that nests validated child catalogue atoms rather than arbitrary markup.

---

## Freeform escape-hatch atom: findings

### 1. The Core Question & Architectural Context

In A2UI's current pipeline, fallback mechanisms operate at two distinct phases:

1. **Late-Stage Render Fallback (`cloud-run-renderer`)**:
   - Atoms are authored using structured, semantic schemas from the ~550-atom catalogue.
   - When a target surface (such as Google Chat's restricted `cardsV2` widget set) cannot render an atom natively, `cloud-run-renderer` runs headless Chromium to produce flat PNG/GIF imagery.
   - Expression remains fully structured; only the render format is degraded.

2. **Domain Vector Escape Hatches (`agent_sketchpad` & `freeform_canvas`)**:
   - `agent_sketchpad` (stage: preview): Progressive multi-stroke SVG canvas built from an ordered array of validated SVG elements (`circle`, `ellipse`, `rect`, `line`, `polyline`, `polygon`, `path`, `g`) animated across multi-turn streaming updates.
   - `freeform_canvas` (stage: preview): One-shot sanitized SVG vector diagram canvas for domain-specific diagrams (topologies, circuits, geometric illustrations) where no discrete atom fits. Enforces a strict SVG allowlist, rejects all script/foreignObject/external URLs, and mandates plain-text `summary` and `justification` fields.

The central exploration question is: **Can and should this validated-freeform pattern generalize one step earlier into a universal expression fallback for arbitrary UI layout and content?**

---

### 2. The Inherent Tension: The "Path of Least Resistance" Failure Mode

Every design system with an open-ended generic container or unstructured custom-content slot inevitably encounters the "path of least resistance" trap:

- **Model Steering Degradation**: When agents have access to an unconstrained fallback, LLM prompt routing and function calling quickly gravitate toward dumping unstructured layout blobs rather than selecting structured, domain-specific atoms (`metric_callout`, `task_timeline`, `status_badge`, `gauge_sla`).
- **Surface Portability Loss**: Structured atoms map deterministically to diverse surfaces (Web HTML/CSS, Google Meet Stage panels, Apps Script Web dialogs, MCP-Apps webviews, Google Chat card widgets, email-safe inline HTML, and print/PDF stylesheets). An unconstrained freeform expression cannot be translated into native host widgets and forces all non-web surfaces to either break or invoke heavy headless rendering.
- **Accessibility & Downstream Semantic Reasoning**: Structured atoms expose machine-readable semantic properties (`value`, `status`, `threshold`, `trend`). Freeform blobs obscure this semantic graph, preventing downstream A2A peer agents, screen readers, test harnesses, and automated data extractors from inspecting, parsing, or binding to derived state.
- **Security Surface Explosion**: While SVG vector geometry can be securely constrained using a tight tag and attribute allowlist with local `#fragment` references, a general UI/layout escape hatch requires complex HTML/CSS layout (boxes, flex/grid, text styling, interactions), dramatically expanding the attack surface for mutation XSS, CSS exfiltration, DOM clobbering, and external resource leakage.

---

### 3. Architectural Recommendation: Three-Tier Hierarchy

We recommend preserving a clear three-tier separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Structured Catalogue Atoms (~550 atoms)             │
│ - Primary semantic vocabulary for all interactive agent UI  │
│ - Full surface portability, accessibility & state binding   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Bounded Vector Escape Hatches                       │
│ - agent_sketchpad (progressive streaming SVG sketches)      │
│ - freeform_canvas (one-shot sanitized SVG diagrams)        │
│ - Mandatory justification, summary, strict SVG allowlist    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Late-Stage Render Fallbacks (cloud-run-renderer)    │
│ - Universal rasterization fallback at the RENDER layer      │
│ - Translates structured atoms to flat images for Chat/cards │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Specification for a Compound Layout Atom (`declarative_layout`)

If a broader compound arrangement mechanism is ever needed to compose multiple catalogue atoms without authoring one-off custom atoms, it should be designed as a **`declarative_layout` atom**, NOT an arbitrary HTML/SVG escape hatch.

#### Schema Definition

```yaml
- type: declarative_layout
  stage: preview
  description: 'A structured multi-slot composite container allowing agents to compose
    existing catalogue atoms into flex or grid arrangements when no dedicated composite
    atom exists. Does NOT allow raw HTML/CSS/scripts; children must be valid catalogue atom objects.'
  compact_description: structured flex/grid container composing existing catalogue atoms
  surfaces:
    works_on:
    - web
    - google-apps-script-web
    - mcp-apps
    degraded_on:
    - surface: google-chat
      note: Flattened to sequential cards or rendered via cloud-run-renderer image fallback
    - surface: email
      note: Converted to HTML table grid
  fields:
    summary: 'string (required). Accessibility label and fallback summary describing the compound layout.'
    justification: 'string (required, minimum 20 characters). Why existing composite atoms (e.g. metric_grid, dashboard_row) are insufficient.'
    layout: 'string (optional, default "row"). One of "row", "column", "grid_2col", "grid_3col", "split_sidebar".'
    gap: 'string (optional, default "md"). One of "none", "sm", "md", "lg".'
    align_items: 'string (optional, default "stretch"). One of "start", "center", "end", "stretch".'
    slots: 'array of objects (required). Each slot is {slot_id: string, width?: string, atom: object}. atom must be a valid, schema-compliant catalogue atom dict.'
```

#### Example Payload

```json
{
  "type": "declarative_layout",
  "summary": "Deployment overview showing cluster health metric alongside recent build trace",
  "justification": "Needs side-by-side juxtaposition of real-time SLA gauge and streaming tool call trace not covered by existing dashboard atoms.",
  "layout": "split_sidebar",
  "gap": "md",
  "slots": [
    {
      "slot_id": "sidebar",
      "width": "300px",
      "atom": {
        "type": "gauge_sla",
        "value": 99.8,
        "max_value": 100,
        "label": "Cluster Availability"
      }
    },
    {
      "slot_id": "main",
      "atom": {
        "type": "tool_call_card",
        "tool_name": "k8s_rollout_status",
        "status": "success",
        "args": "{\"deployment\": \"ingress-controller\", \"namespace\": \"prod\"}",
        "result": "Deployment ingress-controller successfully rolled out (3/3 replicas up)."
      }
    }
  ]
}
```

#### Mandatory Guardrails

1. **Child Atom Registry Validation**: Every item inside `slots[].atom` must validate against `atoms/schema.yaml` and pass through the canonical `_RENDERERS` registry.
2. **Nesting Depth Cap**: Recursion depth is strictly capped at 1 (`depth <= 1`) to prevent uncontrolled DOM nesting and responsive breakages.
3. **Closed Design Tokens**: Spacing, alignment, and distribution are governed exclusively by closed enums (`gap`, `layout`, `align_items`), completely blocking inline CSS strings or raw DOM injections.
