# Circle Pack

Part-to-whole as packed circles: each item is a circle whose area shows its value, and the optional per-item path (1 to 3 group names, top down) nests the circles inside outlined group circles, so a budget, a skills inventory or a folder tree reads as clusters. Laid out by d3-hierarchy pack() (circle packing: the front-chain placement of packSiblings and the smallest enclosing circle of packEnclose, padding 3) on the server, so there is no script. A group's hue follows its top-level group and a deeper circle is a lighter shade of it; group circles are outlined, leaf circles are filled. Every circle carries its name, path, value and share in a hover title and in the hidden table (item, path, value, share of total), and the aria label gives the total, the number of groups and the largest item. A leaf name (and its value, in a wider container) is drawn inside the circle where it fits, and a group name at the top of its circle where it fits; both are 12 px text gated on the container width. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-depth --k, so a motion_timeline track on p builds it level by level from the groups inward and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| items | array (required, 2 to 60) of {path (optional, array of 0 to 3 strings, max 20 each: the item's ancestor groups from the top down; same shape as the treemap's nested mode and the sunburst), name (max 24, default "Item n"), value (number above 0)}. An item without a usable path is a circle of its own at the top level. Items with a value of 0 or less, a value that is not a finite number, or that are not an item are dropped and counted in a note; items beyond the first 60 are noted and not drawn. With fewer than 2 usable items a note replaces the chart. |
| unit | string (optional, max 12). Appended to every value in the title, the aria label, the labels and the hidden table. |
| version | integer (optional, default 1). The circle_pack contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "circle_pack"
}
```

Live page: https://a2uicatalog.ai/atoms/circle_pack/
Full field contract: https://a2uicatalog.ai/spec.json
