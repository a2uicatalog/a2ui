# Voronoi

Nearest-site regions of a set of points: the plot is split into one region per site, each region being every spot that is closer to its site than to any other site (a catchment or service area: which store, depot, sensor or office is nearest). Regions come from a Delaunay triangulation and its Voronoi cells (d3-delaunay, with delaunator and robust-predicates), clipped to the sites' extent plus a margin, with nice axis ticks in the data's own units. Each region is filled with a light colour by group (a legend names every group, never colour alone) or with one light fill and a visible outline when there are no groups; the site is a dot, and its label sits under the dot when the region is wide enough for it (otherwise the label is hidden; the full label is in the region's tooltip and in the table). Static SVG, no script, scaled to its container. The hidden table lists every site with x, y, group, value and its share of the area. The aria label gives the number of sites, the number of groups and the site with the largest region. Motion-ready: each region reads --p through a --k so a motion_timeline track on p fades the regions in one after another; the standalone render is the finished picture.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| sites | array (required, 3 to 200) of {x, y (numbers, required), label (optional, max 24), group (optional, max 20), value (optional number)}. A site whose position equals an earlier site's is merged into the first, with a note. An entry that is not an object with finite numeric x and y (or beyond 1e12) is left out and counted in a note; entries beyond the first 200 are noted and not used; fewer than 3 sites at different positions gets a note instead of the chart. A label or group that is a number is shown as that number; a list, object or boolean is no text (the site is called "Site 1", "Site 2" ... by its place in the list, and has no group). value is shown in the table and in the region's tooltip only, never drawn. |
| x_label | string (optional, max 30). Under the plot. |
| y_label | string (optional, max 30). Above the plot. |
| unit | string (optional, max 12). Appended to the values in the table and the tooltips. |
| version | integer (optional, default 1). The voronoi contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "voronoi"
}
```

Live page: https://a2uicatalog.ai/atoms/voronoi/
Full field contract: https://a2uicatalog.ai/spec.json
