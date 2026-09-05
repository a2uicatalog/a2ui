# Preview Frame

An iframe whose `src` is driven by a wire, so picking a value elsewhere on the page re-navigates it CLIENT-SIDE — no server round trip, no paint_result, nothing else on the page repainted.
A DATA atom, same spirit as sortable_list: it renders whatever src it is given and reacts to whatever is wired into it; it has no opinion on what the iframe shows. Meant to sit next to a picker (menu/select) and a StringTemplate primitive that turns the picked value into a URL — e.g. a "preview this before you commit it" panel, where committing is a SEPARATE, ordinary action.
Same-origin only in practice: nothing here relaxes sandboxing. A cross-origin src is subject to the embedded page's own frame-ancestors / X-Frame-Options exactly as any other iframe.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| src | string (optional). Initial iframe URL. Empty renders the placeholder instead of an iframe. Normally left empty and driven entirely by `wire.src`. |
| label | string (optional). A small heading above the frame. |
| height | number (optional). Frame height in px. Default 320. |
| emptyMessage | string (optional). Shown in the placeholder before a src exists. Default "Nothing selected yet." |

## Example payload

```json
{
  "type": "preview_frame"
}
```

Live page: https://a2uicatalog.ai/atoms/preview_frame/
Full field contract: https://a2uicatalog.ai/spec.json
