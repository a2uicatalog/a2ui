# Photo Grid

A clickable image grid: every tile is both a photo and a row.
Built to close a real gap — data_table has no way to show what a row IS, only what it says about itself, so a photo-driven decision (which wallpaper, which chair) forced a text table plus a separate "View photo" link plus a separate select-then-tap-a-button flow before an action could fire. This atom is the shape that removes all three: the thing you look at and the thing you click are the same element.
Reuses data_table's onRowClick contract exactly — same data-row-json attribute, same _a2uiBindRowClicks binder, same array-wire form for "select AND immediately run an action" in one tap (shipped 2026-08-04 for onRowClick, inherited here for free rather than rebuilt). A DATA atom, not a domain one, same reasoning sortable_list gives for its own genericness: it renders whatever {id, url, ...} objects it is given and fires whatever the caller wired onRowClick to, so the same atom serves a voting board, a photo picker, or a product chooser without a second named atom per use case.
`badge` and `active` exist because a click-driven UI still has to show its OWN state back — a starred tile that does not visibly read as starred after the tap is a button that looks like it did nothing. Both are plain strings/booleans the caller derives server-side (a star count, a "you picked this" flag); the atom does not compute either.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| images | array (required). Objects of {id, url, alt?, caption?, badge?, active?}. `id` is what data-row-json carries back to onRowClick (along with every other field on the object — the WHOLE row, same contract data_table's onRowClick already has). `caption` overlays the bottom of the tile. `badge` is a short string pinned top-right (a count, a status) — omit it for no badge. `active` outlines the tile and tints its badge to mark "this one is in a selected/chosen state" from the caller's own point of view. |
| cols | integer (optional, default 3). 2-4 reads best; more than 4 on a phone-width viewport crowds captions into illegibility. |

## Example payload

```json
{
  "type": "photo_grid",
  "images": 1
}
```

Live page: https://a2uicatalog.ai/atoms/photo_grid/
Full field contract: https://a2uicatalog.ai/spec.json
