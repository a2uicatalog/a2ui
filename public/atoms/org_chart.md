# Org Chart

A hierarchy built from a list of nodes with parents, drawn as boxes in tiers joined by connector lines (layout "tree", the default), as a dendrogram with every leaf on the last tier (layout "cluster"), or as a radial tree with the root at the centre and rotated labels (layout "radial"). It is a real nested list in every layout, so it reads in order to a screen reader. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-item --k, so a motion_timeline track on p builds it item by item and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not measured | 2026-11-13 | no example payload in the gate data |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| nodes | array (required, 3 to 30) of {id (max 24), label (max 28), parent_id (max 24, empty for the root)}. One root; at most four tiers and six children per node. Several top-level nodes are drawn under an undrawn root. |
| layout | string (optional, "tree", "cluster" or "radial", default "tree"). "tree" is the tidy tree (d3 tree). "cluster" is a dendrogram (d3 cluster) with the same boxes, labels and caps; every leaf sits on the last tier whatever its depth and a parent is centred over its children; there is no distance or height field, so tier spacing carries no meaning. "radial" is d3's radial tidy tree with the root at the centre, small dots for nodes and the label outside each dot, turned along its branch and never upside down. Any other value draws the tree. |
| version | integer (optional, default 1). The org_chart contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "org_chart",
  "title": "Engineering leadership",
  "nodes": [
    {
      "id": "1",
      "label": "VP Engineering",
      "parent_id": ""
    },
    {
      "id": "2",
      "label": "Staff architect",
      "parent_id": "1"
    },
    {
      "id": "3",
      "label": "Director, core",
      "parent_id": "1"
    },
    {
      "id": "4",
      "label": "Director, apps",
      "parent_id": "1"
    },
    {
      "id": "5",
      "label": "Data lead",
      "parent_id": "3"
    },
    {
      "id": "6",
      "label": "Frontend lead",
      "parent_id": "4"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/org_chart/
Full field contract: https://a2uicatalog.ai/spec.json
