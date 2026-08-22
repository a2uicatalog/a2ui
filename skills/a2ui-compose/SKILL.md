---
name: a2ui-compose
description: Compose an A2UI payload (typed atom blocks) and render it into real HTML — a chart, dashboard, status board, decision tree, or any structured UI, once the right atoms are already known (see the a2ui-catalog skill for picking them). Use when asked to SHOW something rather than describe it, and the host can display HTML or open a link. Not for connecting a new agent/host to the MCP server itself (see a2ui-mcp).
license: MIT
metadata:
  author: a2uicatalog
  version: "1.0.0"
---

# Composing and rendering an A2UI payload

## The payload shape

```json
{
  "title": "Weekly numbers",
  "theme": "light",
  "blocks": [
    { "type": "heading", "text": "This week" },
    { "type": "stat_card", "value": "1,234", "label": "Daily users", "delta": "+12%" }
  ]
}
```

`blocks` is an ordered array of atoms (the "blocks dialect"). A v1.0 `createSurface`
envelope (templates + dataModel bindings) is also accepted wherever a payload is taken —
`theme` is `light`, `dark`, or `terminal` (the catalog's own dark/monospace brand skin).

## Render, by host capability

- **MCP Apps-capable host** (renders inline in the conversation, no URL, no size
  ceiling): `render_surface(payload)`.
- **Any other MCP host**: `preview_url(payload)` — a shareable link on the shared demo
  renderer (rate-limited: 10 calls per client per 7 days).
- **No rate limit, your own deployment**: `make_surface_url(payload, renderer_url)` —
  renders against a renderer YOU deployed (see the self-hosting quickstart below), or
  omit `renderer_url` for the encoded-fragment + BYO guidance.
- **Protocol-free, no MCP client at all**: `POST https://a2uicatalog.ai/api/render` with
  the payload as the JSON body — returns a complete self-contained HTML page. Same
  guards, same 50-requests/day-per-IP limit as the MCP tools above. `POST
  /api/render/batch` does up to 25 payloads in one call with PARTIAL SUCCESS semantics
  (one malformed payload doesn't fail the batch).

## Failure modes worth knowing before they surprise you

- **Preview-stage or unpublished atoms** aren't an error — they render as a visible
  "not published here" notice rather than being silently dropped, and are named in the
  `X-A2UI-Unpublished` response header.
- **Atoms that need a render-time server fetch** (`data_source`, `firestore_read`,
  `doc_ai_summary`, `multi_doc_ai_brief`, `gemini_handoff`) are refused with 400 on the
  public renderer — deploy your own renderer for those (see below).
- **Limits**: 256 KB body, 300 blocks, 12 levels of nesting on `/api/render`. An
  oversized or over-nested payload is a 400, not a silent truncation — check the error
  body for which limit was hit.
- **A surface query param** (`?surface=web|mcp-apps|google-apps-script-web|google-meet-stage`)
  applies that surface's declared compatibility policy: atoms marked `degraded_on` still
  render (named in `X-A2UI-Degraded`); atoms marked `incompatible_on` are replaced with a
  visible callout (named in `X-A2UI-Incompatible`) rather than rendering something wrong.
  `pdf`, `email` and `google-chat` are refused with 400 here — this endpoint emits HTML,
  and answering half-honestly about portability on those surfaces is worse than refusing.

## Self-hosting for unlimited rendering

The shared demo renderer and `/api/render` are both rate-limited by design. Deploy your
own Google Apps Script renderer in four commands, at no cost beyond a Google account, and
every subsequent `make_surface_url` call targets it instead — unmetered:

```bash
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-schema-renderer
clasp login && clasp create --type webapp && clasp push && clasp deploy
```

## Reference

| Document | URL |
|---|---|
| OpenAPI specification | https://a2uicatalog.ai/openapi.json |
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Self-host guide | https://a2uicatalog.ai/renderer |

Free, MIT licensed, no signup. Independent, unofficial project — not affiliated with,
endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is
Anthropic's. Source: https://github.com/a2uicatalog/a2ui
