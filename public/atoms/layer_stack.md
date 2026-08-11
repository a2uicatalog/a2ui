# Layer Stack

Declarative labelled layers for a layered architecture — a protocol stack, a request path, any "what lives at which level" picture. Each layer is a band carrying a mono technical fact (`field`) beside a plain-language gloss (`note`) — primitive_plate's labelling pairing, without its image substrate: a primitive_plate pin annotates a REAL capture and must never annotate a hand-drawn illustration, and an abstract stack has no capture to pin. Two things concept_ladder cannot do: declare `columns` and each layer renders its `cells` side by side, so ONE stack carries a per-layer comparison of two systems; and set a layer or cell to `status: absent` and it renders a visibly hollow, dashed band, so a level a system does NOT define reads as a stated absence rather than an omission from the diagram. Shares article_journey / concept_ladder's palette token system and IBM Plex fonts so the explainer atoms read as one design system. renderers/web_article.py is the reference implementation; apps-script-surface/gas-wired-renderer/atoms_layers.gs is the port that carries it to every other surface (GAS ?p= URLs, the MCP Apps bundle and the Worker's /api/render all compile from the .gs sources).

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Main heading. |
| eyebrow | string (optional). Small uppercase label above the title. |
| dek | string (optional). Italic one-line subtitle under the title. |
| caption | string (optional). One prose line under the header, before the stack. Backtick spans render as inline code. |
| source | object (optional) — same attribution bar as concept_ladder {title, url, author?, publication?, published?, read_minutes?, label?, steered_by?}. Set it whenever the stack describes SOMEONE ELSE'S system, so the artifact reads as a piece ABOUT that system rather than one that could stand in for its documentation. |
| order | string (optional). 'bottom_up' (default) or 'top_down'. Which end of the picture the FIRST declared layer lands at. bottom_up puts it at the bottom — the wire/transport end — so the array reads the way a stack is spoken aloud, from the bottom up. Badge numbering always follows the declared order, not the visual one. |
| base_label | string (optional). Axis caption printed under the stack, e.g. "bytes on the wire". |
| top_label | string (optional). Axis caption printed above the stack, e.g. "meaning". |
| columns | array (optional). Each item {label, accent?} — a column header. When present, every layer's `cells` render side by side beneath these headers, which is how one stack carries a per-layer comparison of two systems. Omit (or give one column) for a plain single stack. `accent` is a CSS colour string for that column's header and rule. Each label ALSO repeats quietly inside every cell of its column: the header row is a long way up by the time you reach the bottom band, colour cannot carry column identity because the cell fill already encodes `status`, and a band stays self-describing when rendered alone by ComponentId. The repeat is suppressed on a band that spans all columns, and on single-column stacks. |
| layers | array (required). Each item is a stack_layer atom object (see that type) — also independently addressable by ComponentId when emitted in the A2UI v1.0 ChildList wire format, so a live agent can patch one layer without resending the whole surface. |
| theme | string (optional). 'light' (default) or 'dark' — selects the base palette before any per-token overrides. |
| palette | object (optional). Same token set as article_journey and concept_ladder: paper, paper_raised, ink, ink_soft, line, accent, accent_soft, blocked, blocked_soft, cleared, cleared_soft, mono_bg, mono_fg, mono_accent — each a CSS colour string. Unset tokens keep the theme default. `status` maps onto these: present -> cleared, absent -> blocked, partial -> accent. |
| use_plex_fonts | boolean (optional, default true). Loads IBM Plex Mono and IBM Plex Serif via same-origin @font-face — see THIRD-PARTY-NOTICES.md. Set false for system font stacks only. |

## Example payload

```json
{
  "type": "layer_stack",
  "layers": []
}
```

Live page: https://a2uicatalog.ai/atoms/layer_stack/
Full field contract: https://a2uicatalog.ai/spec.json
