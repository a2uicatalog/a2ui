# Photo Stepper

A full-viewport, one-photo-at-a-time lightbox with prev/next and a vote button per slide — the sibling photo_grid does not cover: reviewing options ONE AT A TIME with full attention, immersively, rather than scanning a grid. Neither replaces the other; pick per use case, or offer both. Renders closed as a compact trigger card (first photo + label); clicking it opens the full takeover.
The takeover itself is a pure-CSS checkbox toggle — the SAME `#checkbox:checked ~ .overlay{display:...}` pattern the `css_modal` atom already uses for its own position:fixed;inset:0 overlay, not a new mechanism. Paging within the open overlay is the SAME pure-CSS radio-input trick the existing `carousel` atom already uses (sibling :checked selectors drive the slide transform) — no JS-tracked index to go stale, and critically, nothing for a live data refresh to disturb: `carousel` never had a live-update wire to worry about, but this atom does, and the radio's own browser-owned :checked state surviving a vote untouched is what stops "vote on photo 12, get silently bounced back to photo 1" from ever being possible in the first place — not a bug that was fixed, a failure mode the design does not have. Same reasoning protects open/closed state: the checkbox is the browser's own state too, so a live update cannot close the overlay out from under you either.
That is also why this atom's live-update path (_a2uiUpdatePhotoStepper) is NOT a rebuild like photo_grid's own _a2uiUpdatePhotoGrid — it patches each slide's badge/vote-button/voter-line IN PLACE, matched by candidate id (not array position), and touches nothing else. Matching by id, specifically, because the typical consumer of this atom (a live vote board) re-sorts its candidate list by vote count on every read while voting is open — so a candidate's position in the incoming array can move the instant ANY vote lands, including the one just cast on the slide currently open; patching by position against a reordered array would silently swap a different candidate's photo/name into the slide the radio's :checked state still has open. A consequence worth knowing before using this atom: because the update path patches EXISTING slide elements rather than creating them, the caller should populate the initial `images` prop with real data at render time (server-side), not rely purely on the `rows` wire to populate an empty first paint — an update arriving before any slide exists to patch has nothing to act on.
Reuses photo_grid's click contract exactly for the vote button (same data-row-json attribute, same generalised [data-row-json] binder in A2UIState.html) — the third consumer of a mechanism built once for data_table's own onRowClick.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| images | array (required). Objects of {id, url, alt?, name?, price_display?, badge?, active?, starred_by_display?, source_url?}. Same shape family as photo_grid (id/url/badge/active carry the identical meaning), plus fields specific to a one-at-a-time review: `name`/`price_display` render as the slide's caption title/subtitle, `starred_by_display` is a plain pre-joined string (e.g. "Curtis, Marianne") shown under the caption, `source_url` (optional) renders a plain "Open source listing" link in the caption when present — the atom does not aggregate voter names or validate the link itself, the caller derives both server- side, same reasoning photo_grid gives for `badge` and `active` being caller-derived rather than computed by the atom. |
| accent | string (optional, hex, default #0f766e). Vote-button and active- badge colour. |
| trigger_label | string (optional, default "Browse full screen"). Label shown on the closed trigger card, next to the photo count. |

## Example payload

```json
{
  "type": "photo_stepper"
}
```

Live page: https://a2uicatalog.ai/atoms/photo_stepper/
Full field contract: https://a2uicatalog.ai/spec.json
