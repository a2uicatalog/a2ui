import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { config } from './config.js';
import { adapters } from './adapters/registry.js';
import { handleMcp } from './routes/mcp.js';
import { handleServerCard } from './routes/wellknown.js';
import { handleHealthz } from './routes/healthz.js';
import { selfCheckChatAuth } from './lib/chat-auth.js';

const app = new Hono();

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
