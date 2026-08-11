# Architecture: a2h Printer

This repo is one repo, two entrypoints, one shared core: `src/` (self-hosted
Slack/Teams/Chat/MCP, this document's main subject) and `copilotkit/` (the hosted
CopilotKit Channels bridge — see `copilotkit/README.md` for its own architecture).
Both sign against the same `RENDER_SIGNING_KEY` via `src/lib/crypto-utils.js`'s
`signRenderUrl` — the "printer" — and hit the same public `a2ui-renderer-public`
service; that's the one piece genuinely shared between the two modes.

**Why siblings, not one merged into the other's adapter registry** (the pattern
documented below): the `PlatformAdapter` contract's `registerRoutes(app)` assumes
every platform is an inbound webhook mountable on one shared Hono `app` — true for
Slack/Teams/Chat/Telegram, not true for CopilotKit. CopilotKit's Channels SDK is the
opposite shape: an outbound, LLM-agent-driven process that owns its own runtime
(`createCopilotNodeListener`) and decides what to render via tool-calling, not a
request handler reacting to one. Forcing it into this registry would mean either
lying about the contract (a "route" that's actually a whole second server) or
weakening the registry's honest "routes are mountable on our app" guarantee for every
platform to accommodate the one that doesn't fit. Two sibling entrypoints sharing one
signing core avoids both.

## The self-hosted platform-adapter registry (`src/`)

This package started Slack-only, gained Teams, then Chat, with Telegram sketched (not
built) as a fourth. Rather than re-deriving "how do I add a platform" by reading four
route files each time, this document describes the pattern once.

## Why this exists

The [original v1 design doc](/home/curtis/.claude/plans/cuddly-yawning-brook.md)
explicitly deferred generalizing this package into a reusable pattern, flagged as
"worth doing once a second surface actually needs it, not before (YAGNI)." Teams became
that second surface and the generalization didn't happen — visible as a hardcoded
if/else ladder in `routes/mcp.js` and duplicated business logic between
`routes/command.js` and `routes/teams.js`. Chat becoming the third surface, with
Telegram named as a fourth, was the actual trigger point that doc set. This is that
generalization, done as an *additive* layer over the existing code rather than a
rewrite — every platform's original route/lib files are untouched in shape, just
wrapped.

## The contract

`src/adapters/registry.js` exports `adapters`, an array of `PlatformAdapter` objects:

```js
/**
 * @typedef {Object} PlatformAdapter
 * @property {string} id                          'slack' | 'teams' | 'chat' | ...
 * @property {() => boolean} isConfigured          required env present? no side effects
 * @property {() => string[]} missingConfig        names of unset required vars — never values
 * @property {(app: Hono) => void} registerRoutes  mounts THIS platform's own routes + auth middleware
 * @property {(...ids) => string} ownerKey         builds this platform's storage owner_key
 * @property {(args: object) => string|null} ownerKeyFromMcpArgs
 *   inspects /mcp's caller-supplied args shape, returns an owner_key if THIS platform
 *   recognizes it, else null
 */
```

Three call sites consume this array, and adding a platform means writing one new
`adapters/<platform>.js` and adding it to `registry.js` — nothing else changes:

- **`src/server.js`**: `for (const adapter of adapters) adapter.registerRoutes(app)`
- **`src/routes/mcp.js`**: `ownerKeyFrom(args)` loops over
  `adapter.ownerKeyFromMcpArgs(args)` until one matches — this replaced the original
  hand-written Slack-then-Teams if/else, the concrete symptom that motivated this
  whole registry.
- **`src/routes/healthz.js`** (`GET /status`): loops over `adapter.isConfigured()` /
  `missingConfig()` to report what's live, without ever echoing secret values.

### Why `registerRoutes(app)`, not a generic `verify(req)` hook

Each platform's inbound auth is genuinely shaped differently — the registry does NOT
try to unify them behind one hook, because that unification would be false:

| Platform | Auth shape | Where verified |
|---|---|---|
| Slack | HMAC-SHA256 over the **raw** request body, computed **before** any JSON/form parsing (Slack signs bytes, not a re-serialized object) | Middleware, `adapters/slack.js`'s `withSlackSignature` |
| Teams | Per-request RS256 JWT, verified against Bot Framework's JWKS via `jose` | Inside the handler, `routes/teams.js` (needs the parsed body's claims-adjacent context) |
| Chat | Per-request JWT, TWO verification paths depending on configured audience mode (see below), via `google-auth-library` | Inside the handler, `routes/chat.js` |
| Telegram (sketched, not built) | Static shared-secret header (`X-Telegram-Bot-Api-Secret-Token`) — no signature math at all | Would be middleware, like Slack |

`registerRoutes(app)` hands each adapter the raw Hono `app` and lets it wire its own
middleware/handler shape. This is deliberate: forcing "auth = JWT" or "auth = HMAC" as
the only two possibilities is exactly the kind of premature unification that would need
undoing the moment a fifth platform showed up with yet another shape.

### Routes are mounted unconditionally

An unconfigured platform's routes still exist — they return a `501
{"error": "... not configured"}` per request, not a bare 404. A deployer pointing a
Slack/Azure/Chat console at a URL for a platform they haven't finished configuring gets
something to actually debug.

## Shared business logic: `lib/command-handler.js`

`help | whoami | list | show | weather` is implemented ONCE, in `runCommand()`, shared
by `routes/command.js` (Slack), `routes/teams.js`, and `routes/chat.js`. Each route file
shrinks to: verify auth → parse the platform's own envelope → build a few closures →
call `runCommand` → format the platform's own reply.

**Diffing the two original (pre-extraction) copies turned up three GENUINE
divergences, not just formatting noise** — worth knowing before assuming "the platforms
behave identically":

1. **Help/unknown-command text differs in wording** (Slack: backtick-wrapped
   `` `/a2ui <cmd>` `` slash-command syntax; Teams/Chat: plain quoted `"<cmd>"`, no
   slash concept) — caller-supplied via `helpText()`/`unknownText()` closures.
2. **`list`'s per-item bullet format differs** (Slack: `` • `id` — title ``; Teams/Chat:
   `- id — title`) — caller-supplied via `listLineFor(reading)`.
3. **`show`/`weather` SUCCESS behavior is a real behavioral difference, not wording**:
   Slack sends an explicit ephemeral confirmation IN ADDITION to the channel post (its
   reply channel is separate from the post target). Teams and Chat stay silent on
   success — the card/image post itself IS the visible confirmation — and only reply on
   failure. `runCommand` never adds a reply after `renderReading`/`postWeather`
   resolve; those closures decide entirely for themselves, per platform.

If you extract a NEW shared command in the future and platforms diverge again: keep the
divergence in `runCommand` as an explicit parameter if it's a single tunable value;
push it back into the per-platform closure if it's closer to behavior than formatting.
Don't let a platform's quirk become an unlabeled special case inside the "shared"
function — that recreates the exact un-auditable-duplication problem this file exists
to remove.

## Storage: one owner-key namespace per platform

`src/storage/index.js` exports `slackOwnerKey`, `teamsOwnerKey`, `chatOwnerKey` —
`"<platform>:<tenant-or-org-id>:<user-id>"`. Distinct prefixes so identities from
different platforms can never collide, in storage or in `MCP_ALLOWED_OWNERS`. No
cross-platform identity linking exists or is planned — a Slack user and a Teams user of
the same human are, and remain, unrelated identities (v1 design decision #1).

Each platform picks the most STABLE identifier pair it has, not the most convenient
display one:

- Slack: `team_id` + `user_id` (both real Slack IDs)
- Teams: `tenantId` + AAD `aadObjectId` (preferred over the display-only `from.id`)
- Chat: Space resource name (`spaces/AAAA...`) + User resource name
  (`users/1234567890...`)

## Google Chat specifics

Chat has **no native atom candidates** — `cardsV2`'s widget set is fixed, no custom
layout, no charts beyond what Google ships (confirmed against the live
`cloud-run-renderer/server.py`, which established this same print-channel pattern for
Chat first). So there is no `chat-blocks.js`/`chat-mapping.js`, no bucket-ladder audit
like Slack got — every atom always goes through the image-render fallback
(`lib/render-to-chat.js` → `lib/crypto-utils.js`'s `signRenderUrl`, the same
platform-agnostic HMAC scheme Slack's own D-bucket fallback uses, verified
byte-identical to the Python reference in `cloud-run-renderer/server.py`).

**Inbound** (`lib/chat-security.js`) verifies a `POST /chat` really came from Google —
TWO genuinely different paths depending on the Chat app's configured "Authentication
Audience" mode:

- **App URL** (string audience): standard Google OIDC signing keys, verified via
  `google-auth-library`'s `OAuth2Client.verifyIdToken()`, THEN a separate check that
  `payload.email === 'chat@system.gserviceaccount.com'` — never `payload.iss`, which
  for a Google-signed ID token is a fixed Google issuer regardless of which service
  account issued it, so it can never distinguish Chat's SA from any other caller.
- **Project Number** (numeric audience): Chat's own service-account x509 certs
  (`CHAT_CERTS_URL`, not JWKS-shaped), verified via
  `verifySignedJwtWithCertsAsync()`. Here `iss` DOES carry the identity signal.

Plus Cloud-Run-platform-level gotchas (apply to any Node service on Cloud Run, nothing
Chat-specific): the bearer can arrive on `Authorization` OR
`X-Serverless-Authorization`; the scheme arrives lowercased (`bearer `) after Cloud
Run's own rewrite; on an IAM-gated deployment Cloud Run strips and replaces the JWT's
real signature before forwarding, so cryptographic verification only works on
`--allow-unauthenticated` (which Chat needs anyway, for its anonymous image-fetch
second hop from the rendered card).

**Outbound / proactive posting** (`lib/chat-auth.js`) is a THIRD distinct outbound-auth
shape, different from Slack's static bot token and Teams' OAuth2 client-credentials
flow: Google Chat's app-authenticated `spaces.messages.create` requires the caller to
be the SPECIFIC service account registered as the Chat app's own identity — not just
any GCP principal. `google-auth-library`'s `GoogleAuth` (Application Default
Credentials) resolves this with zero key file on Cloud Run, but ONLY if the service was
deployed with `--service-account=<that specific SA>` (`deploy.sh`'s
`CHAT_SERVICE_ACCOUNT` var does this) — ADC does not make "any attached SA" work,
Chat requires that one.

## Telegram: the design-validation checkpoint (not built)

Telegram's real webhook auth is a static shared-secret header
(`X-Telegram-Bot-Api-Secret-Token`, set via `setWebhook`) — no HMAC-over-body, no JWT.
Simplest of the four:

```js
export const telegramAdapter = {
  id: 'telegram',
  isConfigured: () => Boolean(config.telegramBotToken && config.telegramWebhookSecret),
  registerRoutes(app) {
    app.post('/telegram/webhook', async (c, next) => {
      const got = c.req.header('X-Telegram-Bot-Api-Secret-Token') || '';
      if (!config.telegramWebhookSecret || !safeEqual(got, config.telegramWebhookSecret)) {
        return c.text('unauthorized', 401);
      }
      await next();
    }, handleTelegramUpdate);
  },
  ownerKey: (chatId, userId) => `telegram:${chatId}:${userId}`,
  ownerKeyFromMcpArgs: (args) =>
    (args.chat_id && args.user_id) ? telegramOwnerKey(args.chat_id, args.user_id) : null,
};
```

This drops into the registry with **zero changes** to `registry.js`, `server.js`, or
`routes/mcp.js` — the actual proof the contract generalizes, not just an assertion that
it should. Building it for real would additionally need: `lib/telegram-blocks.js` (a
compiler — Telegram's Bot API has a real formatted-message/inline-keyboard surface,
richer than Chat's fixed cards, so it likely does NOT need to be always-image the way
Chat is; unconfirmed, would need its own classify pass like Slack got), a
`command-handler.js` closure set (`routes/telegram.js`), and a decision on whether
Telegram's inline-keyboard callbacks get a Slack-style interactivity handler.

## The MCP JSON-RPC dispatcher (`routes/mcp.js` / `lib/mcp-tools.js` / `lib/jsonrpc.js`)

v1.1 replaced `/mcp`'s original flat `{tool, args}` endpoint with a real MCP (Model
Context Protocol) JSON-RPC 2.0 server, split three ways:

- **`src/routes/mcp.js`** — the dispatcher: bearer-token auth (unchanged from v1.0),
  `MCP-Protocol-Version` header handling (accept-and-negotiate, not reject-on-mismatch),
  and the `initialize`/`notifications/*`/`ping`/`tools/list`/`tools/call` switch. Also
  still owns `ownerKeyFrom(args)` (the adapter-registry loop, see above) and the
  `MCP_ALLOWED_OWNERS` allowlist check — relocated from the old handler, not rewritten.
- **`src/lib/mcp-tools.js`** — this deployment's own 7-tool catalogue (`save_reading`,
  `list_readings`, `delete_reading`, `render_reading_to_{slack,teams,chat}`,
  `render_decision_interactive`) plus the executor that runs one by name against an
  already-resolved store.
- **`src/lib/jsonrpc.js`** — the two envelope-shape helpers (`mcpResult`/`mcpError`).

**The dispatch shape (`initialize`/`tools/list`/`tools/call` switch, JSON-RPC error
codes) ports an existing, proven pattern already live elsewhere in this estate — it
isn't invented here.** The *tool catalogue* is authored fresh (it's this package's own
7 tools, not a general-purpose one), but the protocol plumbing around it is a port, not
a fresh design.

**Deliberately NOT batch-capable**: single JSON-RPC requests only. JSON-RPC batching
was removed from the MCP spec as of `2025-06-18` and stays removed in this endpoint's
pinned revision (`2025-11-25`, see `mcp-tools.js`) — LLM-agent callers send one call at
a time regardless, so this is complexity avoided, not a capability given up.

**Two-tier error mapping** (apply this rule anywhere `/mcp` is touched): auth failure →
real HTTP `401`, because it happens before any JSON-RPC body is parsed. Everything past
auth is HTTP `200`, with JSON-RPC semantics living in the body — a malformed request
(bad JSON, unknown method) is a JSON-RPC protocol error; a *valid* request whose tool
execution fails (bad owner args, owner not allowlisted, a render call throwing) is a
`tools/call` **result** with `isError: true`, never a JSON-RPC-level error. Conflating
these two would make a caller unable to tell "you sent garbage" from "you asked for
something that failed" — don't merge them back into one shape in a future pass.

**Owner-identity args live in each tool's `description`, not its formal `inputSchema` —
a deliberate tradeoff, not an oversight.** Putting `team_id`/`tenant_id`/`space_name`
etc. into `inputSchema` as a hardcoded `oneOf` of platform shapes would re-introduce the
exact per-platform coupling the adapter registry exists to eliminate: a future 4th
platform adapter would then require editing every tool's schema too, not just adding
one `adapters/<platform>.js`. The honest cost, on record so a future pass doesn't "fix"
this by folding the fields into `inputSchema`: a client that validates purely against
`inputSchema` (rather than reading `description`) discovers the requirement on its
first `tools/call` — as a normal `isError:true` result naming the missing fields — not
upfront via schema validation.

**`GET /.well-known/mcp/server-card.json`** (`src/routes/wellknown.js`) is generated
per-request, not a static file — a self-hosted deployment has no fixed public URL known
at build time, unlike a hosted single-tenant manifest. `serverUrl` prefers
`config.publicBaseUrl` (`PUBLIC_BASE_URL` env var) when set, falling back to the
inbound request's `Host` header only when it isn't. This order is deliberate, not
incidental: reflecting an attacker-influenceable `Host` header into a discovery
document that agents then POST bearer tokens at would be the same fail-open shape
`TRUST_CLOUD_RUN_IAM`'s fail-closed-when-unset pattern (`chat-security.js`) already
exists to avoid elsewhere in this codebase. No `agent-card.json` is shipped — an
AgentCard implies A2A protocol participation, this endpoint speaks MCP only, and
nothing here consumes or requires one; add it back only if a real consumer shows up.

**Not built here, on purpose** (see README's "MCP protocol" section for the deployer-
facing version of this): a native CopilotKit adapter (CopilotKit's Channels SDK routes
through CopilotKit's own hosted backend — enabling it inside this package would defeat
the self-hosted premise for any deployer who turned it on) and a full ADK-agent-wrapper
(superseded elsewhere in this estate by pointing ADK's own MCP client at a standards-
compliant server instead — the same fix this endpoint now offers for free to any MCP
client, ADK included).

## Dev-only auth bypasses

`TEAMS_DEV_BYPASS_AUTH` / `CHAT_DEV_BYPASS_AUTH` let `scripts/smoke/{teams,chat}.sh`
exercise those routes without a live Bot Framework/Chat app registration. Both are
gated with `NODE_ENV !== 'production'` **at the verification call site**, not just in
the config value — so the flag is structurally inert in any image built with
`NODE_ENV=production` (the `Dockerfile`'s default), regardless of what the env var is
set to. This mirrors the "guard only if configured, fail closed and loud if not" shape
`TRUST_CLOUD_RUN_IAM` also uses — a prior version of exactly the weaker shape (guard
only if configured, no hard fail-safe) left a Cloudflare Worker open once elsewhere in
this estate.

## Testing one platform in isolation

`scripts/smoke/{slack,mcp,teams,chat}.sh` — each is self-contained, computes real
signatures/tokens where that's possible offline (Slack's HMAC is pure Web Crypto, no
live app needed), and uses the dev bypasses above where it isn't (Teams/Chat's real
auth needs a live JWKS/cert endpoint). Run against a locally-started instance:

```sh
PORT=8080 SLACK_SIGNING_SECRET=... MCP_AUTH_TOKEN=... node src/server.js &
SLACK_SIGNING_SECRET=... ./scripts/smoke/slack.sh
MCP_AUTH_TOKEN=... ./scripts/smoke/mcp.sh
```

`teams.sh`/`chat.sh` take a `--bypass-armed` flag you must pass explicitly — matching
whatever the server was actually started with — since a script can't inspect a
different process's launch environment.

## Critical files

- `src/adapters/registry.js` — the contract + the array every call site iterates
- `src/adapters/{slack,teams,chat}.js` — one descriptor per platform
- `src/lib/command-handler.js` — the shared business logic
- `src/storage/index.js` — owner-key factories
- `src/lib/{slack,teams,chat}-security.js` — inbound auth, one per platform
- `src/lib/chat-auth.js` — Chat's outbound (proactive-posting) credential
- `src/lib/crypto-utils.js` — `signRenderUrl` (shared HMAC render-signing) + `safeEqual`
- `src/routes/mcp.js` — the MCP JSON-RPC dispatcher (auth, protocol-version handling,
  the `initialize`/`tools/list`/`tools/call` switch, owner-key resolution)
- `src/lib/mcp-tools.js` — this deployment's 7-tool MCP catalogue + executor
- `src/lib/jsonrpc.js` — JSON-RPC envelope helpers
- `src/routes/wellknown.js` — `GET /.well-known/mcp/server-card.json` discovery manifest
