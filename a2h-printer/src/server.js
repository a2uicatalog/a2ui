import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { config } from './config.js';
import { adapters } from './adapters/registry.js';
import { handleMcp } from './routes/mcp.js';
import { handleServerCard } from './routes/wellknown.js';
import { handleHealthz } from './routes/healthz.js';
import { selfCheckChatAuth } from './lib/chat-auth.js';
import { createRateLimiter } from './lib/rate-limit.js';

const app = new Hono();

// Defense-in-depth only — see rate-limit.js's own header comment. TWO
// separate limiter instances (own bucket Map each), applied to their own
// route groups — NOT one shared global limiter (round-1 version, fixed
// 2026-08-12): Slack/Teams/Chat webhooks all arrive from that platform's
// own shared infrastructure IP, so a busy workspace's real traffic must
// not compete for the same budget /mcp needs, and vice versa. /status and
// the .well-known discovery doc stay unthrottled — pure reads, no state
// changed, and CI/monitoring traffic shouldn't need to reason about a
// rate limit at all.
const webhookLimiter = createRateLimiter({ maxPerWindow: config.rateLimitWebhookMaxPerWindow });
const mcpLimiter = createRateLimiter({ maxPerWindow: config.rateLimitMcpMaxPerWindow });
app.use('/mcp', mcpLimiter);
app.use('/slack/command', webhookLimiter);
app.use('/slack/interactivity', webhookLimiter);
app.use('/api/messages', webhookLimiter);
app.use('/chat', webhookLimiter);

// Boot-time echo of the SAME check teams-security.js/chat-security.js each
// make per-request — those are the real enforcement (structurally inert
// whenever NODE_ENV!=='production'), this is just making the state visible
// BEFORE the first request, not a second gate. Roast-panel finding,
// 2026-08-12: the Dockerfile's NODE_ENV=production is the only thing
// standing between "bypass disabled" and "wide open," and the README's own
// "runs anywhere Docker runs" claim means someone deploying via a bare
// `node src/server.js` (skipping the Dockerfile) could forget to set it
// with no warning until this line existed.
if ((config.teamsDevBypassAuth || config.chatDevBypassAuth) && process.env.NODE_ENV !== 'production') {
  console.warn(
    '[boot] WARNING: a dev auth-bypass flag is set (TEAMS_DEV_BYPASS_AUTH/' +
    'CHAT_DEV_BYPASS_AUTH) and NODE_ENV is not "production". Inbound auth ' +
    'is BYPASSED for the affected platform(s). Never run this combination ' +
    'on a deployment reachable by anyone but you.');
}

// NOT /healthz: that exact literal path is swallowed by Google's edge (GFE)
// ahead of Cloud Run — confirmed empirically 2026-08-08 (curl to /healthz
// returns Google's generic "Error 404 (Not Found)!!1" HTML with no
// x-cloud-trace-context header, while /health, /Healthz, /healthz/, and any
// other path all correctly reach this app and get Hono's own 404). Renamed
// to sidestep the collision rather than fight it.
app.get('/status', handleHealthz);

// MCP surface is a separate trust boundary from the platform routes below —
// see routes/mcp.js. Always mounted, unlike the platform adapters: it's not
// a "platform" in the Slack/Teams/Chat sense, and MCP_AUTH_TOKEN stays
// required() in config.js (a deliberate scope boundary, not an oversight —
// see config.js's header comment).
app.post('/mcp', handleMcp);
// Discovery manifest for MCP clients — see routes/wellknown.js for why this
// is generated per-request rather than a static file.
app.get('/.well-known/mcp/server-card.json', handleServerCard);

// Each platform adapter owns its own routes AND its own auth middleware —
// see adapters/registry.js's PlatformAdapter contract for why this isn't a
// single generic verify(req) hook. Routes are mounted UNCONDITIONALLY
// (matching Teams' original pattern): an unconfigured platform's routes
// still exist and return a diagnosable 501, rather than a bare 404 that
// looks identical to "wrong URL" to whoever's configuring the other end.
for (const adapter of adapters) adapter.registerRoutes(app);

serve({ fetch: app.fetch, port: config.port }, (info) => {
  console.log(`a2uicatalog a2h Printer (self-hosted mode) listening on :${info.port}`);
  // Non-blocking: a misattributed outbound Chat credential should surface
  // as a clear log line at deploy time, not delay the port opening or crash
  // a deployment that only uses Chat's inbound webhook-reply path (a valid,
  // common shape — see chat-auth.js's own comment on why this never throws).
  selfCheckChatAuth();
});
