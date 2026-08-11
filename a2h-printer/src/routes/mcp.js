// POST /mcp — real MCP (Model Context Protocol) JSON-RPC 2.0 endpoint.
// This is how an agent (Claude, ADK, or anything else with an MCP client)
// gets content into this self-hosted instance and posts it to Slack/Teams/
// Chat. v1.1: replaces the old flat {tool,args} shape outright (breaking
// change, not a dual-mode shim — see README's "Upgrading to v1.1" section
// for the migration snippet; the old shape's own header comment already
// flagged it as a temporary v1 simplification, never a stable contract).
//
// Dispatch SHAPE (initialize/tools/list/tools/call switch, JSON-RPC error
// codes) is ported from the estate's existing production MCP server
// (a2ui-private/gas-mcp/Mcp.gs's _mcpDispatch) — proven pattern, not
// reinvented here. The tool catalogue itself (lib/mcp-tools.js) is this
// package's own 7 tools, authored fresh.
//
// Auth: a single shared bearer token (config.mcpAuthToken) — unchanged from
// v1.0. This is the one place an HTTP status code is the right signal: it
// happens BEFORE any JSON-RPC body is parsed. Everything past auth returns
// HTTP 200, with JSON-RPC semantics living entirely in the response body —
// see the two-tier error mapping below.
//
// Single JSON-RPC requests only — no batch-array handling. The 2025-06-18
// spec removed JSON-RPC batching and 2025-11-25 (this endpoint's pinned
// revision — see lib/mcp-tools.js) keeps it removed; LLM-agent callers send
// one call at a time regardless, so this is dead weight avoided, not a
// capability given up.
//
// Ownership: every tools/call must specify team_id+user_id (Slack) /
// tenant_id+user_id (Teams) / space_name+user_id (Chat) inside its
// arguments (there's no platform-signed request here to derive them from,
// unlike /slack/command) — the caller says whose store to read/write. See
// lib/mcp-tools.js's OWNER_ARGS_NOTE for why these live in each tool's
// description, not its formal inputSchema.
import { getStore } from '../storage/index.js';
import { config } from '../config.js';
import { safeEqual } from '../lib/crypto-utils.js';
import { adapters } from '../adapters/registry.js';
import { mcpResult, mcpError, PARSE_ERROR, METHOD_NOT_FOUND, INTERNAL_ERROR } from '../lib/jsonrpc.js';
import { MCP_PROTOCOL, MCP_SERVER_INFO, MCP_INSTRUCTIONS, mcpToolDefs, mcpCallTool } from '../lib/mcp-tools.js';

// Was a hand-written if/else ladder (Slack shape, then Teams shape) — the
// exact duplication pattern that motivated the adapter registry (see
// adapters/registry.js). Now a loop: each adapter's ownerKeyFromMcpArgs
// recognizes its own args shape or returns null. Adding a platform means
// writing one new adapters/<platform>.js — zero lines change here.
function ownerKeyFrom(args) {
  if (!args) return null;
  for (const adapter of adapters) {
    const key = adapter.ownerKeyFromMcpArgs(args);
    if (key) return key;
  }
  return null;
}

// Resolves owner + allowlist + store exactly as v1.0 did, but every failure
// mode now returns an MCP tool-result with isError:true instead of an HTTP
// error status — see the two-tier error mapping below for why.
async function callToolResolvingOwner({ name, arguments: args = {} } = {}) {
  const ownerKey = ownerKeyFrom(args);
  if (!ownerKey) {
    return {
      isError: true,
      content: [{ type: 'text', text: 'args.team_id+args.user_id (Slack), args.tenant_id+args.user_id (Teams), or args.space_name+args.user_id (Chat) are required' }],
    };
  }

  // Identity gate. The token proves the CALLER may use this deployment; it
  // proves nothing about WHOSE store they may touch, and the owner key here
  // is entirely caller-asserted (see config.mcpAllowedOwners for the full
  // reasoning). When an allowlist is configured, an assertion outside it is
  // refused; otherwise the asserted identity is logged so there is at least
  // an audit trail of who a caller claimed to be.
  if (config.mcpAllowedOwners.length) {
    if (!config.mcpAllowedOwners.includes(ownerKey)) {
      // Log the attempt (this is the signal that a token has leaked or a
      // caller is misconfigured) but do not echo the allowlist back — an
      // unauthorized caller learning which identities exist is free recon.
      console.warn(`[mcp] refused owner_key "${ownerKey}" — not in MCP_ALLOWED_OWNERS`);
      return { isError: true, content: [{ type: 'text', text: 'this token may not act for that identity' }] };
    }
  } else {
    console.warn(
      `[mcp] MCP_ALLOWED_OWNERS is unset — accepting caller-asserted identity ` +
      `"${ownerKey}". Any holder of the bearer token can read or write ANY ` +
      `identity's data. Set MCP_ALLOWED_OWNERS to lock this deployment down.`);
  }

  let store;
  try {
    store = getStore(ownerKey);
  } catch (e) {
    // Fail closed (plan decision #3): a storage-layer misconfiguration must
    // surface as an error, never as "proceed with no data."
    return { isError: true, content: [{ type: 'text', text: (e && e.message) || String(e) }] };
  }

  return mcpCallTool(store, name, args);
}

async function dispatchOne(req) {
  const id = req && req.id !== undefined ? req.id : null;
  const method = req && req.method;
  try {
    switch (method) {
      case 'initialize':
        // capabilities.tools ONLY — no resources/prompts/async workflow
        // capabilities, because none of those are implemented. Deliberate,
        // honest declaration: some MCP clients only call tools/list if
        // `tools` was declared here, so this is load-bearing, not
        // decorative.
        return mcpResult(id, {
          protocolVersion: MCP_PROTOCOL,
          capabilities: { tools: {} },
          serverInfo: MCP_SERVER_INFO,
          instructions: MCP_INSTRUCTIONS,
        });
      case 'notifications/initialized':
      case 'notifications/cancelled':
        return null; // notification — no reply
      case 'ping':
        return mcpResult(id, {});
      case 'tools/list':
        return mcpResult(id, { tools: mcpToolDefs() });
      case 'tools/call':
        return mcpResult(id, await callToolResolvingOwner(req.params || {}));
      default:
        return mcpError(id, METHOD_NOT_FOUND, 'method not found: ' + method);
    }
  } catch (e) {
    return mcpError(id, INTERNAL_ERROR, 'internal error: ' + ((e && e.message) || String(e)));
  }
}

export async function handleMcp(c) {
  const auth = c.req.header('authorization') || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (!token || !safeEqual(token, config.mcpAuthToken)) {
    return c.json(mcpError(null, -32000, 'unauthorized'), 401, { 'WWW-Authenticate': 'Bearer' });
  }

  // Required on HTTP requests after initialize per the 2025-06-18+ spec.
  // Behavior: accept-and-negotiate, not reject-on-mismatch — if a client's
  // header names a version other than MCP_PROTOCOL, this server still
  // responds using its own declared version (initialize's protocolVersion
  // already establishes the session's actual version) rather than hard-
  // failing the request. Friendlier of the two spec-legal behaviors.
  const clientProtocolVersion = c.req.header('mcp-protocol-version');
  if (clientProtocolVersion && clientProtocolVersion !== MCP_PROTOCOL) {
    console.warn(`[mcp] client requested MCP-Protocol-Version ${clientProtocolVersion}; serving ${MCP_PROTOCOL}`);
  }

  let body;
  try {
    body = await c.req.json();
  } catch {
    return c.json(mcpError(null, PARSE_ERROR, 'parse error'));
  }

  return c.json(await dispatchOne(body));
}
