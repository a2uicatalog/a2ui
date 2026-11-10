---
name: a2ui-rest
description: Call the A2UI Atomic Catalog over plain HTTP, with no MCP client — from a script, a CI job or code an agent writes. Covers finding atoms (/ask, /spec.json), turning a request into blocks (/api/compose), rendering to HTML (/api/render, /api/render/batch, async /api/render/jobs), and the version and rate-limit headers. Use when the caller is code, not a chat host. For MCP hosts see a2ui-mcp; for payload design see a2ui-compose.
license: MIT
metadata:
  author: a2uicatalog
  version: "1.0.0"
---

# The A2UI Atomic Catalog over plain HTTP

Base URL `https://a2uicatalog.ai`. No API key, no signup. The full contract is the
OpenAPI 3.1 spec at `/openapi.json`; this skill is the short path through it.

## 1. Find the atoms

- `GET /ask?query=countdown timer` — ranked, typed atom matches for a plain-English
  question (NLWeb). `mode=summarize` adds a one-paragraph answer. 60 requests per IP per day.
- `GET /spec.json` — every atom with its real field contract. Read the fields from here;
  never guess a field name. `GET /catalogue/index.json` is the compact menu.

## 2. Turn a request into blocks (optional)

`POST /api/compose` with `{"prompt": "weekly sales dashboard with a trend chart"}` returns
candidate atom blocks. 20 requests per IP per day. Check the result against `/spec.json`
before rendering; it is a starting point, not a finished payload.

## 3. Render

The payload is `{"title": "...", "theme": "light" | "dark", "blocks": [ ... ]}`.

- `POST /api/render` — returns a complete self-contained HTML page.
- `POST /api/render/batch` with `{"payloads": [ ... ]}` — up to 25 payloads in one call,
  one call against the daily allowance. Partial success: a bad payload gets its own status
  in `results` and the rest still render.
- `POST /api/render/jobs` — the async form. Returns `202 Accepted` with `job_id`, a
  `Location` header and `status_url`. `GET` the status URL until `status` is `done`, then
  `GET` its `result_url` for the HTML. Polling spends no quota. Jobs are kept for one hour.
  Renders finish within the request today, so the first poll already says `done`; poll
  anyway so your code keeps working if rendering moves to a queue.

Add `?surface=web|mcp-apps|google-apps-script-web|google-meet-stage` to apply that surface's
compatibility policy (`X-A2UI-Degraded` and `X-A2UI-Incompatible` name what changed).

## 4. Headers worth reading

- `X-API-Version: 1` on every response. Send the same header on a request to name the
  version your code was built against; an unsupported value gets a 400 that lists the
  supported versions. Breaking changes are announced with `Deprecation` and `Sunset`
  headers at least 90 days apart (`/versioning.md`).
- `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and the IETF `RateLimit-Policy` /
  `RateLimit` pair on the metered routes. Render is 50 requests per IP per day; a `429`
  carries `Retry-After`.
- `Idempotency-Key` on render requests: retrying the same key within 10 minutes returns the
  first response instead of spending quota again.

## Sandbox

There is no separate sandbox host: these endpoints hold no production data and change
nothing, so a test call against production is safe. Its only cost is quota. To try payloads
by hand, use the playground at https://play.a2uicatalog.ai.

## Failure modes

- `400` with a JSON `error` names the limit hit: 256 KB body, 300 blocks, 12 levels of nesting.
- Atoms that need a render-time server fetch (`data_source`, `firestore_read`,
  `doc_ai_summary`, `multi_doc_ai_brief`, `gemini_handoff`) are refused on the public
  renderer; deploy your own (`/renderer`) for those.
- Unpublished or preview atoms render as a visible notice and are named in
  `X-A2UI-Unpublished`, never silently dropped.
