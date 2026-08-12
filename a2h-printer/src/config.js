// Central env-var reader. required() fails fast and loud at BOOT — reserved
// for config with no meaningful "not configured" state (MCP_AUTH_TOKEN
// below: an /mcp endpoint with no token is a bug, not a valid deployment
// shape). Every per-PLATFORM credential (Slack, Teams, Chat, ...) uses
// optional() instead and fails closed per-request in its own adapter — a
// deployer enabling only a subset of platforms must be able to boot with
// the rest entirely unset. See adapters/registry.js.
//
// Prints a clean one-line message and exits, rather than throwing — an
// uncaught Error here surfaces as a raw Node stack trace, which is the
// actual first thing a brand-new deployer following the README sees if
// they miss one line of .env (found in a 2026-08-12 roast-panel pass).
// Still fails exactly as fast and as loud — process.exit(1) is not a
// softer failure mode, just a legible one.
function required(name) {
  const v = process.env[name];
  if (!v) {
    console.error(`\n${name} is required and is not set.\n` +
      `See .env.example for how to generate/obtain it, then set it in your .env.\n`);
    process.exit(1);
  }
  return v;
}

function optional(name, fallback = undefined) {
  return process.env[name] ?? fallback;
}

export const config = {
  port: Number(optional('PORT', 8080)),
  // Optional, NOT required() — matches Teams' existing pattern below rather
  // than crashing boot when Slack alone is unconfigured. A deployer who only
  // wants Teams (or, later, only Chat) must be able to start this process
  // with zero Slack env vars; adapters/slack.js fails closed *per-request*
  // with a clear 501 instead (see its withSlackSignature middleware).
  slackSigningSecret: optional('SLACK_SIGNING_SECRET', null),
  slackBotToken: optional('SLACK_BOT_TOKEN', null),
  slackDefaultChannel: optional('SLACK_DEFAULT_CHANNEL', '#general'),
  // Shared bearer token gating /mcp — replaces the Cloudflare Access/OAuth
  // identity system dropped per plan decision #1 (no separate reader
  // account in v1). Required: an MCP endpoint that posts to a real Slack
  // workspace must not be left open to anonymous callers.
  mcpAuthToken: required('MCP_AUTH_TOKEN'),
  // Overrides the .well-known/mcp/server-card.json serverUrl instead of
  // deriving it from the inbound request's Host header — see
  // routes/wellknown.js's header comment for why the Host-header fallback is
  // a deliberate, named trust assumption rather than a universal default.
  // Only needed on a proxy setup that doesn't forward a trustworthy Host.
  publicBaseUrl: optional('PUBLIC_BASE_URL', null),
  // Storage: SQLite by default (see storage/ layer); DATABASE_URL switches to
  // Postgres behind the same interface. Plan: cuddly-yawning-brook.md #3.
  databaseUrl: optional('DATABASE_URL', null),
  sqlitePath: optional('SQLITE_PATH', './data/a2h-printer.db'),
  // D-bucket image fallback (atoms with no native Slack block — exotic
  // charts, genuinely visual atoms). Both optional TOGETHER: a deployment
  // that omits them keeps today's behavior (render-to-slack.js passes no
  // renderConfig, so a D-bucket atom in the payload fails that whole
  // compile — see its own comment). Set both to enable it; reuses
  // cloud-run-renderer's already-live, already-signed /render.png rather
  // than standing up a second render path (see render-to-slack.js).
  renderSigningKey: optional('RENDER_SIGNING_KEY', null),
  renderBaseUrl: optional('RENDER_BASE_URL', null),
  // Which owner_key(s) the /mcp bearer token is permitted to act for.
  //
  // WHY: /mcp builds the storage key from CALLER-SUPPLIED args.team_id /
  // args.user_id, and the shared bearer token only answers "may you use this
  // deployment at all" — never "are you who you say you are". So any holder
  // of the token can read, write or delete ANY identity's stored content by
  // naming a different user_id. Demonstrated inadvertently 2026-08-08:
  // readings were written under a fabricated identity and under a real Slack
  // identity with the same token, no challenge, no audit distinction.
  //
  // Comma-separated `slack:{team_id}:{user_id}` values. When set, a call
  // naming anything else is refused. Left unset it stays permissive and logs
  // loudly — deliberately NOT fail-closed, because this package is already
  // deployed by third parties whose deployments would break on upgrade, and
  // a security fix that silently bricks running installs is its own
  // incident. Single-workspace deployments (the documented v1 shape) should
  // always set it.
  mcpAllowedOwners: (optional('MCP_ALLOWED_OWNERS', '') || '')
    .split(',').map((s) => s.trim()).filter(Boolean),

  // Microsoft Teams surface — optional, same posture as Slack's vars above
  // (both now optional(), not required()). Unset -> routes/teams.js fails
  // closed per-request with a clear "not configured" error, not a startup
  // crash — mirrors renderSigningKey/renderBaseUrl's optional-pair pattern.
  teamsAppId: optional('TEAMS_APP_ID', null),
  teamsAppPassword: optional('TEAMS_APP_PASSWORD', null),
  // See teams-auth.js's header comment — 'botframework.com' is correct for
  // a MultiTenant Azure Bot registration (the common case); a SingleTenant
  // registration needs its own home tenant ID here instead.
  teamsAuthTenant: optional('TEAMS_AUTH_TENANT', 'botframework.com'),

  // Dev-only bypass for Teams' inbound JWT verification (see
  // teams-security.js) — lets scripts/smoke/teams.sh exercise the route
  // without a live Bot Framework registration. Structurally inert outside
  // development: teams-security.js ANDs this with `NODE_ENV !== 'production'`
  // at the call site, not just here, so setting this var in a production
  // image (NODE_ENV=production, per the Dockerfile) can never arm it —
  // "guard only if configured" without a hard fail-safe is exactly the shape
  // that left a Cloudflare Worker open once elsewhere in this estate.
  teamsDevBypassAuth: optional('TEAMS_DEV_BYPASS_AUTH', '') === '1',

  // Google Chat surface — optional, same posture as Teams above. Chat has
  // no native block compiler (cardsV2's widget set is fixed — confirmed
  // against cloud-run-renderer/server.py and its own launch post), so
  // adapters/chat.js's isConfigured() requires the render-signing pair
  // below too, not just CHAT_AUDIENCE — "configured but can't render
  // anything" is worse than "not configured".
  //
  // One or two audiences, comma-separated: the "App URL" mode (a string,
  // this service's own /chat URL) and/or the "Project Number" mode (a
  // numeric GCP project number) — see chat-security.js for why these are
  // two GENUINELY different verification paths, not a simplification to
  // unify.
  chatAudiences: (optional('CHAT_AUDIENCE', '') || '').split(',').map((s) => s.trim()).filter(Boolean),
  // Only relevant on a --no-allow-unauthenticated deployment, where Cloud
  // Run strips the inbound JWT's real signature before forwarding — see
  // chat-security.js. Default OFF: a public (--allow-unauthenticated)
  // deployment — the mode Chat needs anyway, for its anonymous image-fetch
  // second hop — must never accept an unsigned token.
  chatTrustCloudRunIam: optional('TRUST_CLOUD_RUN_IAM', '') === '1',
  // Dev-only bypass for Chat's inbound verification, same NODE_ENV-gated
  // shape as teamsDevBypassAuth above — lets scripts/smoke/chat.sh exercise
  // the route without a live Chat app registration.
  chatDevBypassAuth: optional('CHAT_DEV_BYPASS_AUTH', '') === '1',

  // Chat proactive posting (an agent pushing content into a space it isn't
  // currently being messaged in, via /mcp's render_reading_to_chat — see
  // lib/chat-auth.js). Unset = fall back to Application Default
  // Credentials. On Cloud Run this is zero-key-file ONLY if the service was
  // deployed with --service-account=<the Chat app's own registered SA> —
  // Chat's app-authenticated spaces.messages.create requires that SPECIFIC
  // identity, not just any attached SA. Only set this explicitly on
  // non-GCP hosts (Fly.io/Render/bare VPS), which have no attachable
  // service identity at all.
  chatServiceAccountKey: optional('GOOGLE_SERVICE_ACCOUNT_KEY', null),
};
