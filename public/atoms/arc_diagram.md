# Arc Diagram

Connections between named things as arcs: the nodes sit on one horizontal line and each link is a semicircle above it joining its two nodes (the d3 gallery "arc diagram"), so a co-authorship list, a module-dependency graph or a who-talks-to-whom table reads as clusters of short arcs and a few long ones. Node positions are even steps along the line (d3-scale scalePoint with padding 0.5) and the arcs are static SVG, so there is no script. Arc thickness shows the link value (1 to 6 px; all links at 2 px when every value is equal). The optional node group sets the dot and the arc colour (an arc takes its source node's) and a legend names every group, but colour is never the only cue: every dot and arc carries its name, group, link count or value in a hover title, and the hidden tables list every node with its group and link count and every link with its two ends and value. The aria label gives the node and link counts and the most connected node. Node names hang below the line rotated 90 degrees; in a narrow container only every second, fourth or eighth name is drawn (the first always) so that none overlaps. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a --k, so a motion_timeline track on p draws the arcs and then the nodes and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| nodes | array (required, 2 to 40) of {id (string, max 40: what links refer to), label (string, max 24, default the id), group (optional string, max 20)}. An entry that is not a node, has no id or repeats an earlier id is left out and counted in a note; entries beyond the first 40 are noted and not drawn. With fewer than 2 usable nodes a note replaces the chart. |
| links | array (optional, 0 to 120) of {source (a node id), target (a node id), value (optional number above 0, default 1)}. A link that is not an object, joins a node to itself, names an id that is not a node or has a value that is not a finite number above 0 is dropped and counted in a note; links beyond the first 120 are noted and not drawn. Links are undirected: the arc is always drawn above the line between its two nodes. Parallel links are drawn on top of one another. |
| order | "input" (default), "group" or "degree". input keeps the order of nodes; group sorts by group name and then label (a node without a group first; plain code-unit comparison, ties keep the input order); degree puts the most connected node first (ties keep the input order). Any other value is input. |
| unit | string (optional, max 12). Appended to every link value in the titles and the hidden table. |
| version | integer (optional, default 1). The arc_diagram contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "arc_diagram"
}
```

Live page: https://a2uicatalog.ai/atoms/arc_diagram/
Full field contract: https://a2uicatalog.ai/spec.json
