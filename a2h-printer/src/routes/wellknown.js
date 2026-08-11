// GET /.well-known/mcp/server-card.json — MCP discovery manifest.
//
// Unlike a2uicatalog.ai's hosted manifest (a fixed domain baked into a
// static file), a self-hosted deployment has no fixed public URL known at
// build time — it's Cloud Run, Fly.io, a bare VPS, whatever the deployer
// chose. So this is generated PER-REQUEST, not a static file.
//
// serverUrl resolution, deliberately in this order (PUBLIC_BASE_URL first):
// reflecting an attacker-influenceable Host header into a discovery document
// that agents then POST bearer tokens at would be the same fail-open shape
// already closed off elsewhere in this codebase (see chat-security.js's
// TRUST_CLOUD_RUN_IAM, which fails closed when unset rather than trusting an
// unverified header by default). The Host-header fallback below is a named,
// deliberate trust assumption — every documented deploy target for this
// package (Cloud Run, Fly.io, a reverse-proxied VPS) terminates TLS in front
// of the app and forwards a trustworthy Host header — not a silent default a
// deployer has to discover is unsafe. Set PUBLIC_BASE_URL explicitly on any
// proxy setup that doesn't guarantee that.
import { config } from '../config.js';
import { mcpToolDefs, MCP_SERVER_INFO } from '../lib/mcp-tools.js';

export function handleServerCard(c) {
  const base = config.publicBaseUrl || `https://${c.req.header('host') || 'localhost'}`;
  return c.json({
    name: MCP_SERVER_INFO.name,
    displayName: 'a2uicatalog a2h Printer (self-hosted mode)',
    description: 'A self-hosted Slack, Microsoft Teams, and Google Chat bot for a2uicatalog ' +
      'content — save readings and post them to the platforms this deployment has configured. ' +
      'Single-tenant: this server holds one deployer\'s own workspace(s) only.',
    version: MCP_SERVER_INFO.version,
    serverUrl: `${base}/mcp`,
    transport: 'streamable-http',
    protocolVersion: '2025-11-25',
    authentication: { type: 'bearer', required: true },
    tools: mcpToolDefs().map(({ name, description }) => ({ name, description })),
  });
}
