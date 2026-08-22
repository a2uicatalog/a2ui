# Agent Authentication Policy

## MCP server (`a2uicatalog.ai/mcp`)

- **Authentication**: None. No API key, no signup, no OAuth handshake required — connect and call the tools directly.
- **Why**: the server holds nothing to protect; render output belongs to the caller, not us. Capacity is guarded by call limits, not auth.

## Call limits (per tool, not a blanket rate limit)

| Tool | Limit |
|---|---|
| `preview_url` (shared demo renderer) | 10 calls per client (IP-hash) per 7 days |
| `render_surface` / `render_ping` | 300 calls per IP-hash per day |
| `publish_url` | 20 calls per IP per day |
| `/api/compose` (natural-language → atoms) | 20 calls per IP per day |
| All other tools (`list_catalogs`, `get_catalog`, `required_catalogs`, `make_surface_url`, `emit_deployment`) | No per-tool cap — pure computation, no shared resource to protect |

Hitting the `preview_url` limit isn't a dead end: deploy your own Apps Script renderer (see [the quickstart](https://a2uicatalog.ai/llms.txt)) and every subsequent `make_surface_url` call targets it instead of the shared demo — no limit, you own the deployment.

## Enterprise / attributed access (optional, not required for normal use)

Two additional auth paths exist for callers that need per-user attribution rather than anonymous access — neither is needed to use the open `/mcp` endpoint above:

- **HTTP Basic Auth** on `a2uicatalog.ai/mcp-auth` — same tools as `/mcp`, gated.
- **OAuth 2.0** (`a2uicatalog.ai/mcp-oauth/authorize` + `/mcp-oauth/token`) — for platforms (e.g. Gemini Enterprise) whose integration model requires a real OAuth authorization server rather than a static token.

## Web Bot Auth (RFC 9421 message signatures)

Public signing key directory: [`/.well-known/http-message-signatures-directory`](https://a2uicatalog.ai/.well-known/http-message-signatures-directory) — one Ed25519 key (`kid: a2uicatalog-2026-08`). Published so a caller can verify a request signed with this domain's key came from us. Not yet required or checked on any inbound path — the public `/mcp` endpoint stays unauthenticated as described above regardless of whether a request is signed.
