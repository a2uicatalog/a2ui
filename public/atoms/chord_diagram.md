# Chord Diagram

Flows between a few entities in both directions as a circle: each group is an arc on the ring (its length is the flow that leaves it) and each ribbon joins two groups, its width at each end showing the flow from that group to the other, so migration between regions, traffic between services or trade between countries reads at a glance. Laid out by d3-chord chord() with sorted subgroups and drawn with d3-shape arc() and d3-chord ribbon() paths on the server, so there is no script. With the optional directed true the same matrix is laid out by chordDirected() and every flow is an arrow (ribbonArrow()) from the sending group to the receiving one, so direction is drawn instead of read from two widths. Each group has its own hue and a ribbon takes the colour of its source group at reduced opacity; every ribbon carries "A to B: value (B to A: value)" (one direction when directed) in a hover title, and the hidden tables list every non-zero flow (from, to, value) and each group's total out and in; the aria label gives the number of groups, the total flow and the largest flow. Group names sit outside the ring, rotated to read outward and never upside down, shortened with an ellipsis where they do not fit and left out where a neighbour is too close (a visible legend always names every group). Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-group --k, so a motion_timeline track on p builds it group by group and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| groups | array (required, 2 to 12) of strings (max 20 each) naming the entities. A name that is not a string or a number is shown as "Group n". Groups beyond the 12th are noted and not drawn, and their rows and columns are dropped. With fewer than 2 groups a note replaces the chart. |
| matrix | array of rows (required): square, one row and one column per group, numbers 0 or more; the cell at row i and column j is the flow from group i to group j (the diagonal is a flow from a group to itself, drawn as a loop). A matrix that is not a list, not square, or whose size does not match groups is replaced by the note "A chord diagram needs a square matrix with one row per group." and what was wrong. A cell that is negative or not a finite number counts as 0 and is counted in a note. If every flow is 0 a note replaces the chart. |
| unit | string (optional, max 12). Appended to every value in the titles, the aria label and the hidden tables. |
| directed | boolean (optional, default false). false draws chord(): one ribbon joins each pair of groups and its width at each end is the flow from that group (the larger direction is the ribbon's source). true draws chordDirected() with ribbonArrow(): one arrow per non-zero flow, pointing at the receiving group, and a group's arc covers what it sends and what it receives. Any value other than the boolean true is drawn as false. |
| version | integer (optional, default 1). The chord_diagram contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "chord_diagram",
  "groups": 1,
  "matrix": 1
}
```

Live page: https://a2uicatalog.ai/atoms/chord_diagram/
Full field contract: https://a2uicatalog.ai/spec.json
