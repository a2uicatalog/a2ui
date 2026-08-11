# a2uicatalog a2h Printer

Every atom a2uicatalog can compose down to one thing every chat host understands: a
signed, deterministically-rendered image — the "printer." That mechanism is the shared
core behind two independent ways to put a2uicatalog content in front of people:

- **Self-hosted mode** (this directory's `src/`) — a Slack bot, a Microsoft Teams bot,
  and a Google Chat bot, one install, run on your own infrastructure, any combination
  enabled purely by which env vars you set. No a2uicatalog.ai account, no Cloudflare,
  and no workspace data leaves your own deployment — every message, saved reading, and
  interaction stays inside the container and database you control. See
  `ARCHITECTURE.md` for how the platform-adapter registry behind "any combination
  enabled by config" actually works.
- **CopilotKit Channels mode** (`copilotkit/`) — a hosted, LLM-agent-driven surface
  using CopilotKit's Channels SDK, reaching Slack/Telegram/Teams live-proven,
  WhatsApp built but not yet live-tested, Discord unbuilt — through natural-language
  tool-calling instead of fixed commands (includes a `fetch_weather` tool for live
  data, not just static-prop rendering). **Not sovereign** — it runs through
  CopilotKit's own hosted "Intelligence" backend, a deliberately separate trust
  model from self-hosted mode above. See `copilotkit/README.md`.

Both modes sign against the same `RENDER_SIGNING_KEY` and hit the same public
`a2ui-renderer-public` service (`src/lib/crypto-utils.js`'s `signRenderUrl`) — the
printer itself needs no new infrastructure to add a second delivery mode.

This is a deliberately narrow v1 for self-hosted mode: one Slack workspace, one Teams
tenant, and/or one Chat organization per deployment, no cross-surface account linking,
no live catalog sync. See `plan` notes in this repo's history for the full set of
decisions and why each one was made.

## What it does

- Receives Slack slash commands (`/a2ui list`, `/a2ui show <id>`) and interactive
  component clicks (buttons, modals) at signed public HTTP endpoints.
- Receives Microsoft Teams messages ("list", "show <id>") at a single Bot Framework
  endpoint, and compiles saved content into real Adaptive Cards.
- Receives Google Chat messages ("list", "show <id>") at a single Chat API endpoint,
  and renders saved content as images (Chat's `cardsV2` widget set is fixed — no
  custom layout, no charts beyond what Google ships — so every atom goes through the
  same signed-image-render fallback Slack uses for its own exotic atoms; see
  `ARCHITECTURE.md`). Can also POST into a Chat space proactively (outside any
  inbound message) once an outbound service-account credential is configured.
- Exposes a real MCP (Model Context Protocol) JSON-RPC endpoint at `/mcp` so any
  MCP-capable agent — Claude, an ADK agent, or anything else with an MCP client — can
  save content and post it to Slack, Teams, or Chat as a formatted message. See
  "MCP protocol" below.
- Stores everything locally — SQLite by default, Postgres optional. Slack, Teams, and
  Chat identities are stored in separate namespaces (`slack:...` / `teams:...` /
  `chat:...`) and never share data with each other or with a2uicatalog.ai.
- `GET /status` reports which platforms are actually configured (booleans and missing
  env-var names only — never secret values) — the fastest way to confirm what a given
  deployment has enabled.

## Enabling / disabling platforms

Every platform — Slack, Teams, Chat — is entirely optional and controlled purely by
which env vars you set; there is no separate "which platforms" switch to flip. Set a
platform's required vars (see its setup section below) to turn it on; leave them all
unset to leave it off. `MCP_AUTH_TOKEN` is the one exception — it's always required,
since it gates the agent-facing `/mcp` endpoint, which isn't a "platform" in this
sense.

An unconfigured platform's HTTP routes still exist (they're not conditionally
unmounted) but reply with a clear `501 {"error": "... not configured"}` rather than a
bare 404 — so pointing a Slack/Teams/Chat console at a URL for a platform you haven't
finished configuring gives you something to actually debug, not a generic "not found."

`GET /status` is the fastest way to see what's actually live on a given deployment:

```json
{
  "ok": true,
  "platforms": {
    "slack": { "configured": true,  "missing": [] },
    "teams": { "configured": false, "missing": ["TEAMS_APP_ID", "TEAMS_APP_PASSWORD"] },
    "chat":  { "configured": false, "missing": ["CHAT_AUDIENCE", "RENDER_SIGNING_KEY", "RENDER_BASE_URL"] }
  },
  "storage": { "backend": "sqlite" },
  "render_fallback": { "configured": false }
}
```

Only booleans and env-var *names* ever appear — never values, so this is safe to check
without leaking secrets.

The mechanism behind this — one small "adapter" module per platform, all implementing
the same contract, iterated by `src/server.js` and `src/routes/mcp.js` — is documented
in `ARCHITECTURE.md`, including a worked (not-built) Telegram sketch proving the
contract isn't secretly shaped around Slack/Teams/Chat's specific auth mechanisms.

## MCP protocol

`POST /mcp` speaks real MCP — JSON-RPC 2.0, protocol revision `2025-11-25`, pinned
independently of any other MCP server in this estate (dispatch *shape* is ported from a
proven internal pattern; the version string isn't, deliberately — see
`src/lib/mcp-tools.js`). Auth is a single shared bearer token (`MCP_AUTH_TOKEN`) — paste
it into your agent framework's MCP server config the same way you'd paste a Slack bot
token. `initialize` declares `capabilities: { tools: {} }` only (no resources, prompts,
or async workflows — none are implemented); `tools/list` returns this deployment's 7
tools (`save_reading`, `list_readings`, `delete_reading`, `render_reading_to_slack`,
`render_reading_to_teams`, `render_reading_to_chat`, `render_decision_interactive`).
Single JSON-RPC requests only — no batch-array support (removed from the spec itself as
of `2025-06-18`, and LLM-agent callers send one call at a time regardless).

A discovery manifest is served at `GET /.well-known/mcp/server-card.json`, generated
per-request against the actual deployment host (or `PUBLIC_BASE_URL`, if you've set one
for a proxy that doesn't forward a trustworthy `Host` header).

**Upgrading to v1.1**: the old flat `{tool, args}` shape is gone — this is a breaking
change, not a dual-mode shim (the old shape's own header comment already flagged it as a
temporary v1 simplification, never a stable contract). Migrate any custom tool-calling
code:

```jsonc
// v1.0 (removed):
POST /mcp  { "tool": "save_reading", "args": { "team_id": "...", "user_id": "...", "reading": {...} } }

// v1.1:
POST /mcp  { "jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": { "name": "save_reading",
                          "arguments": { "team_id": "...", "user_id": "...", "reading": {...} } } }
```

Owner-identity fields (`team_id`+`user_id`, etc.) are documented in each tool's
`description`, not its formal `inputSchema` — a deliberate tradeoff so adding a future
platform touches zero tool definitions (see `src/adapters/registry.js`'s "one new
adapter file, nothing else changes" contract). A client that validates purely against
`inputSchema` will discover the requirement on its first `tools/call` (as a normal
`isError:true` result naming the missing field), not upfront.

**Integrating with an agent framework:**

- **Google's ADK**: point ADK's own MCP client at this endpoint — no bespoke agent
  wrapper needed. One caveat, precisely scoped: ADK agents running specifically on
  Google's **Agent Runtime** (Gemini Enterprise's hosted execution environment) are
  currently limited to this deployment's image-rendered atoms (Agent Runtime's own UI
  surface doesn't speak A2UI's live rendering protocol) — this is an Agent-Runtime-
  specific constraint, **not** a general ADK limitation. An ADK agent running anywhere
  else against this endpoint has no such restriction.
- **CopilotKit**: intentionally **not** integrated into *this self-hosted mode* — its
  Channels SDK routes all traffic through CopilotKit's own hosted "Intelligence"
  backend, which would mean self-hosted-deployment content silently leaving the
  deployer's own infrastructure, the exact promise this mode exists to keep. That's
  what `copilotkit/` (sibling directory, see top of this README) is for instead — a
  separate, opt-in, explicitly-not-sovereign mode, never folded into this endpoint by
  default. If a self-hosted deployer wants their own saved readings reachable from a
  CopilotKit-connected agent too, the way to do that is pointing `copilotkit/`'s agent
  at THIS deployment's own `/mcp` (a second, additive `mcpServers` entry) — an explicit
  choice to accept CopilotKit's hosted-backend trust model for that one integration,
  never automatic.

## Quickstart (local)

```sh
npm install
cp .env.example .env   # fill in MCP_AUTH_TOKEN, plus whichever platform(s) you want —
                        # see .env.example's own comments, or "Enabling / disabling
                        # platforms" above
npm start
```

Or with Docker:

```sh
cp .env.example .env
docker compose up --build
```

## Slack app setup

1. Create a new Slack app at api.slack.com/apps (from scratch, one workspace).
2. **OAuth & Permissions** → add the `chat:write` bot scope (minimum). Install to your
   workspace, copy the Bot User OAuth Token (`xoxb-...`) into `SLACK_BOT_TOKEN`.
3. **Basic Information** → copy the Signing Secret into `SLACK_SIGNING_SECRET`.
4. **Slash Commands** → create `/a2ui`, Request URL = `https://<your-deployment>/slack/command`.
5. **Interactivity & Shortcuts** → turn on, Request URL = `https://<your-deployment>/slack/interactivity`.

Your deployment must be reachable over HTTPS at the URL you enter.

## Teams app setup

Structurally different from Slack — Teams doesn't call your bot directly, it goes
through Azure Bot Service (Bot Framework), which authenticates itself with a signed JWT
rather than Slack's shared-secret HMAC scheme. More moving parts, but each one is a
one-time setup step, not ongoing maintenance.

1. **Register the bot**: in the Azure Portal, create an **Azure Bot** resource (or an app
   registration directly in Microsoft Entra ID — the Azure Bot resource wizard does both
   for you). Choose **Multi Tenant** unless you specifically need Single Tenant (if you do,
   set `TEAMS_AUTH_TENANT` to your own tenant ID instead of the default). This gives you:
   - An **App ID** → `TEAMS_APP_ID`
   - A **client secret** (Certificates & secrets → New client secret) → `TEAMS_APP_PASSWORD`
2. **Set the messaging endpoint** on the Azure Bot resource to
   `https://<your-deployment>/api/messages`.
3. **Enable the Teams channel**: on the Azure Bot resource's Channels page, add
   Microsoft Teams (off by default).
4. **Create a Teams app package**: a `manifest.json` (declares your bot's App ID, name,
   icons, scope — personal/team/groupChat) plus a color and outline icon PNG, zipped
   together. The **Teams Developer Portal** (Microsoft's own tool,
   [dev.teams.microsoft.com](https://dev.teams.microsoft.com)) will generate all of this
   for you from a form rather than hand-writing the manifest schema.
5. **Install it for testing** — the Developer Portal has a one-click "Preview in Teams"
   for your own account, which is the fastest path and doesn't need any org admin
   involvement. For testing with teammates without a full org rollout: Teams client →
   Apps → "Upload a custom app" (needs custom app upload allowed in Teams Admin Center
   for your tenant — check if this is greyed out).

You do **not** need to submit anything to the public Teams Store just to test — that's a
separate, much heavier Partner Center certification process for public distribution,
not required for personal or team use.

## Google Chat app setup

Structurally the simplest of the three registrations (no manifest, no app store), but
two gotchas are worth more than the rest combined:

1. **Create the Chat app**: [Google Cloud Console](https://console.cloud.google.com) →
   APIs & Services → enable the **Google Chat API** → its **Configuration** tab. Give it
   a name/icon/description.
2. **Connection settings → HTTP endpoint URL**: set to `https://<your-deployment>/chat`.
   (The other options — Apps Script project, Pub/Sub topic, Dialogflow agent — are for
   different architectures entirely; this bundle needs the plain HTTP endpoint.)
3. **Authentication Audience — pick ONE mode, and set `CHAT_AUDIENCE` to match exactly**:
   - **"HTTP endpoint URL"** (the common case): Chat signs its request with a standard
     Google-issued OIDC token, audience = your `/chat` URL itself. Set
     `CHAT_AUDIENCE=https://<your-deployment>/chat`.
   - **"Google Cloud Project number"**: Chat signs with its own service-account x509
     cert instead, audience = the numeric project number (Cloud Console home page).
     Set `CHAT_AUDIENCE=<project-number>`.
   - Both `lib/chat-security.js` verification paths are implemented and can both be
     enabled at once (comma-separated `CHAT_AUDIENCE`) if you're unsure which your
     console will actually send — the code tries each configured audience in turn.
4. **Chat has no native widget richness beyond `cardsV2`'s fixed set** — every saved
   reading renders as one or more images via the same signed-`/render.png` scheme
   Slack's own exotic-atom fallback uses. This means **`RENDER_SIGNING_KEY` and
   `RENDER_BASE_URL` are REQUIRED for Chat**, not optional the way they are for
   Slack/Teams — `GET /status` will show Chat as unconfigured until both are set, even
   with `CHAT_AUDIENCE` present.

### Proactive posting (optional, needs a service account)

An agent (Claude, etc.) can push a saved reading into a Chat space via `/mcp`'s
`render_reading_to_chat` tool, without waiting for that space to message the bot
first — mirroring what `render_reading_to_slack`/`render_reading_to_teams` already do.
This needs Chat's app-authenticated `spaces.messages.create` API, which requires the
caller to be the **specific service account registered as this Chat app's own
identity** (visible on the Configuration page) — not just any GCP principal.

- **On Cloud Run**: pass `CHAT_SERVICE_ACCOUNT=<that-sa>@<project>.iam.gserviceaccount.com`
  to `deploy/cloud-run/deploy.sh` — it deploys with `--service-account`, so Application
  Default Credentials resolve it automatically at runtime, no key file needed.
- **Elsewhere** (Fly.io, Render, a bare VPS — no attachable service identity): generate
  a JSON key for that same service account and set `GOOGLE_SERVICE_ACCOUNT_KEY` to its
  full contents.
- Either way, watch the boot log for `[chat-auth]` — a misattributed credential logs a
  clear warning at startup (before an agent's first real post fails opaquely), not
  silently.

## Deploying

The app itself is platform-agnostic — plain Node/Hono, no `@google-cloud/*`, no
`googleapis`, nothing GCP-specific in `src/` that would tie it to running on GCP. It
runs anywhere Docker runs: Fly.io, Render, a bare VPS with `docker compose up`, AWS App
Runner, etc. — inject the secrets for whichever platform(s) you're enabling as env
vars and mount a volume for `/data` on whichever host you use.

One footnote to "no cloud-vendor SDK": Google Chat support uses `google-auth-library`
(a Google-authored package) — but only to verify Google's own signed tokens and, for
proactive posting, to resolve a Google credential. Neither use requires running on
GCP; `verifyIdToken`/`GoogleAuth` work identically over plain HTTPS from any host. It's
"a library for talking to a Google product," not a hosting requirement — same
reasoning `jose` gets used for Teams' Bot Framework tokens.

**`deploy/cloud-run/`** is the first-class, ready-to-run path for Cloud Run specifically
— a real script (`deploy.sh`), not just docs, handling the bucket + Secret Manager +
`gcloud run deploy` wiring for you. Start there if you're deploying to GCP. Other
platforms don't have a scripted path yet, but the same three ingredients (image, volume,
three env vars) are all any of them need.

### Persistent storage: don't rely on local disk

Cloud Run's local filesystem is ephemeral (in-memory-backed) — it does **not** survive a
redeploy or a cold start after scale-to-zero. `deploy/cloud-run/deploy.sh` mounts a GCS
bucket as a volume so the SQLite file actually persists across deploys; the equivalent on
another platform is whatever persistent-volume mechanism it offers. Skipping this
entirely (pure local disk, no mount) is possible for a throwaway/demo deployment, but
means **every redeploy wipes all saved readings** — not just cold starts, actual code
updates too. Not recommended as a default.

(SQLite under a network-backed volume like GCS-FUSE has some locking caveats under
concurrent writers — irrelevant as long as you keep this to a single instance, which one
workspace's traffic never exceeds anyway. If you outgrow that, switch to Postgres via
`DATABASE_URL` instead of fighting the volume.)

### The `MIN_INSTANCES` decision — read this before deploying

Slack requires an ack within ~3 seconds for slash commands and most interactive
component clicks. Cloud Run containers are not always warm the way Cloudflare Workers
are — a cold start after scale-to-zero can eat that whole budget on its own.

| | `--min-instances 0` (default) | `--min-instances 1` |
|---|---|---|
| Cost when idle | $0 | ~$10/month, continuously, even with zero traffic (checked against Cloud Run pricing, Aug 2026) |
| Risk | The **first** person to trigger the bot after any idle gap (e.g. the first Slack message on a quiet Monday morning) may see Slack's "took too long" timeout. The action often still completes a moment later; a retry works. Everyone right after them hits an already-warm instance and is unaffected — this is not a random ongoing failure rate. | None — always warm. |

Pick whichever tradeoff fits your workspace's traffic and budget. On Cloud Run via
`deploy/cloud-run/deploy.sh`, this is the `MIN_INSTANCES` env var (defaults to `0`):

```sh
MIN_INSTANCES=1 ./deploy.sh   # ~$10/mo, removes the first-after-idle timeout risk
```

On another platform, the equivalent is whatever "always keep N instances warm" setting
it offers.

This app already does what it can to shrink the risk independent of this setting:
slash-command and most button-click responses ack immediately and do their real work via
Slack's `response_url` afterward (see `src/lib/slack-interactivity.js`), so only the
modal-open path (which needs a live `trigger_id`) is actually exposed to cold-start
latency.

## Storage: SQLite by default, Postgres optional

No database server required to try this — `better-sqlite3` ships in the image and reads
`SQLITE_PATH` (defaults to `/data/slack-surface.db`, matching the Cloud Run volume mount
above). Set `DATABASE_URL` to switch backends — **not implemented yet**; the app will
refuse to start with a clear error rather than silently using SQLite anyway if you set
it (`src/storage/index.js`).

## What's out of scope for v1

- No account linking across surfaces (web, Claude, Slack) — Slack's own `team_id:user_id`
  IS the identity here, since a single-workspace self-hosted deployment has no other
  surface to unify with.
- No live catalog sync from a2uicatalog.ai — this ships as a versioned image; update by
  pulling a new tag.
- No Adaptive Card `Action.Submit` handling on Teams yet (`invoke` activities) — Slack's
  decision-tree click-through and modal-open equivalents. `list`/`show` (plain messages)
  are fully wired; interactive card follow-ups are a deliberate v1.1 scope cut, same
  incremental order Slack's own interactivity landed in after its basic commands worked.
- No decision-tree click-through on Chat, and none planned — Chat's `cardsV2` has its
  own button/postback mechanism, but building it would mean a native Chat compiler,
  which directly contradicts why Chat is simple here (no `chat-blocks.js` — see
  `ARCHITECTURE.md`). Out of scope on purpose, not merely deferred.
- No Telegram support yet — sketched, not built, as the concrete proof the platform-
  adapter registry generalizes to a fourth surface with a genuinely different auth
  shape (a static secret header, unlike Slack's HMAC or Teams/Chat's JWTs). See
  `ARCHITECTURE.md` for the sketch and what building it for real would take.
