// Tool catalogue + executor for the /mcp JSON-RPC endpoint (routes/mcp.js).
// This is a self-hosted deployment's OWN 7 tools (save/list/delete/render/
// post-decision-tree) — not a2uicatalog.ai's catalog-browsing set. The
// dispatch SHAPE this endpoint uses is ported from the estate's existing
// production MCP server (a2ui-private/gas-mcp/Mcp.gs's _mcpTools/
// _mcpCallTool) — see routes/mcp.js's header comment — but the tool catalogue
// itself is authored fresh for what this package actually does.
import { renderReadingToSlack } from './render-to-slack.js';
import { renderReadingToTeams } from './render-to-teams.js';
import { renderReadingToChatSpace } from './render-to-chat.js';
import { loadDecisionTree, rootNodeId, buildStepBlocks } from './decision-nav.js';
import { config } from '../config.js';

const POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage';

export const MCP_SERVER_INFO = { name: 'a2uicatalog-a2h-printer', version: '1.1.0' };

// Deliberately pinned to CURRENT STABLE independently of gas-mcp/Mcp.gs's own
// MCP_PROTOCOL ('2025-06-18') — what's ported from that file is the DISPATCH
// SHAPE (initialize/tools/list/tools/call switch, JSON-RPC error codes), not
// its protocol-version string, which was never part of what's proven there.
// gas-mcp and this endpoint are allowed to diverge on version while sharing
// dispatch shape. If this is ever revisited, decide explicitly whether to
// bump both together — don't "resync" this back to 2025-06-18 by assuming
// they were meant to match.
export const MCP_PROTOCOL = '2025-11-25';

export const MCP_INSTRUCTIONS =
  'Self-hosted a2uicatalog Slack/Teams/Chat surface. Tools operate on THIS ' +
  "deployment's own saved readings, scoped by a caller-asserted owner identity " +
  '(team_id+user_id for Slack, tenant_id+user_id for Teams, space_name+user_id ' +
  'for Chat — see each tool description below for exactly which fields it needs). ' +
  'The bearer token proves you may use this deployment; it does not by itself ' +
  'prove which identity you may act as — see this server operator\'s MCP_ALLOWED_OWNERS configuration.';

// Deliberate tradeoff: owner-identity args (team_id/user_id, tenant_id/user_id,
// space_name/user_id) are documented in each tool's `description` below, NOT
// added to `inputSchema` as a hardcoded oneOf of three platform shapes — doing
// that would re-introduce exactly the per-platform coupling the adapter
// registry (adapters/registry.js) exists to eliminate: a future 4th platform
// adapter would then require editing every tool's inputSchema too, not just
// adding one new adapters/<platform>.js. Honest cost of this choice: a client
// that validates purely against inputSchema (rather than reading description)
// will fail its first tools/call instead of knowing the requirement upfront —
// that failure surfaces as a normal isError:true result naming the missing
// owner fields, not a schema-validation rejection. Naming this here is what
// stops a future pass from "fixing" it by folding owner args into inputSchema
// and breaking the zero-edit adapter guarantee this tradeoff protects.
const OWNER_ARGS_NOTE =
  ' Also requires this deployment\'s owner-key fields — team_id+user_id (Slack), ' +
  'tenant_id+user_id (Teams), or space_name+user_id (Chat). See this server\'s ' +
  '/.well-known/mcp/server-card.json or ask the operator which platform(s) are configured.';

export function mcpToolDefs() {
  return [
    {
      name: 'save_reading',
      description: 'Save a reading (an A2UI payload plus metadata) to this deployment\'s storage.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: { reading: { type: 'object', description: 'The reading to save.' } },
        required: ['reading'],
      },
    },
    {
      name: 'list_readings',
      description: 'List saved readings for the calling identity, optionally filtered by runbook.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: {
          runbook: { type: 'string', description: 'Optional runbook filter.' },
          limit: { type: 'number', description: 'Optional max results.' },
        },
      },
    },
    {
      name: 'delete_reading',
      description: 'Delete one or more saved readings by id.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: { ids: { type: 'array', items: { type: 'string' } } },
        required: ['ids'],
      },
    },
    {
      name: 'render_reading_to_slack',
      description: 'Compile a saved reading to Slack Block Kit and post it to a channel.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'Reading id.' },
          channel: { type: 'string', description: 'Slack channel; defaults to this deployment\'s configured default.' },
        },
        required: ['id'],
      },
    },
    {
      name: 'render_reading_to_teams',
      description: 'Compile a saved reading to an Adaptive Card and post it to a Teams conversation.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          service_url: { type: 'string', description: 'Bot Framework service URL for this conversation.' },
          conversation_id: { type: 'string' },
        },
        required: ['id'],
      },
    },
    {
      name: 'render_reading_to_chat',
      description: 'Render a saved reading (image fallback — Chat has no native block compiler) and ' +
        'proactively post it into a Google Chat space.' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          space_name: { type: 'string', description: 'Owning space (also resolves the caller\'s identity).' },
          target_space_name: { type: 'string', description: 'Optional: post to a DIFFERENT space than space_name.' },
        },
        required: ['id', 'space_name'],
      },
    },
    {
      name: 'render_decision_interactive',
      description: 'Post the root step of a saved decision tree as real, clickable Slack buttons ' +
        '(distinct from render_reading_to_slack\'s static one-shot compile).' + OWNER_ARGS_NOTE,
      inputSchema: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          channel: { type: 'string' },
        },
        required: ['id'],
      },
    },
  ];
}

// Entry point for the interactive decision_tree walk (see lib/decision-nav.js
// and lib/slack-interactivity.js's `a2ui_decision_nav:` handler for the
// click-through continuation) — posts the ROOT step as real buttons, distinct
// from render_reading_to_slack's static one-shot compile.
async function renderDecisionInteractive(store, { id, channel }) {
  let tree;
  try {
    tree = await loadDecisionTree(store, id);
  } catch (e) {
    return { ok: false, reason: (e && e.message) || String(e) };
  }
  const startId = rootNodeId(tree.nodes);
  const blocks = buildStepBlocks(tree.readingId, tree.nodes, startId, tree.title);
  const target = channel || config.slackDefaultChannel;
  const resp = await fetch(POST_MESSAGE_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8', authorization: 'Bearer ' + config.slackBotToken },
    body: JSON.stringify({ channel: target, text: tree.title || 'Decision tree', blocks }),
  });
  const out = await resp.json();
  if (!out.ok) return { ok: false, reason: 'Slack post failed: ' + (out.error || 'unknown') };
  return { ok: true, posted_to: target, reading_id: tree.readingId, title: tree.title, slack_ts: out.ts };
}

// Runs one tool by name against an already-resolved store/ownerKey (owner
// resolution + allowlist enforcement stays in routes/mcp.js, same logic as
// before this port, just called from a different site). Returns either
// {content, structuredContent} on success or {isError:true, content} on
// failure — MCP's tool-result envelope, never a thrown exception or a raw
// value; routes/mcp.js's tools/call handler wraps this call in its own
// try/catch only as a last-resort safety net for a bug here, not the normal
// error path.
export async function mcpCallTool(store, name, args = {}) {
  let result;
  try {
    switch (name) {
      case 'save_reading':
        result = await store.save(args.reading || {});
        break;
      case 'list_readings':
        result = await store.list(args.runbook, args.limit);
        break;
      case 'delete_reading':
        result = await store.delete(args.ids);
        break;
      case 'render_reading_to_slack':
        result = await renderReadingToSlack(store, { id: args.id, channel: args.channel });
        break;
      case 'render_reading_to_teams':
        result = await renderReadingToTeams(store, {
          id: args.id, serviceUrl: args.service_url, conversationId: args.conversation_id,
        });
        break;
      case 'render_reading_to_chat':
        // args.space_name is ALSO used by routes/mcp.js's ownerKeyFrom to
        // resolve which store this call touches — that's the reading's OWNER
        // identity, not necessarily where the agent wants to push it now.
        // target_space_name is a distinct, optional override for the actual
        // post target; defaulting to space_name keeps "post back into the
        // same space it came from" the zero-config common case, matching
        // render_reading_to_slack's/_teams' own default, while still allowing
        // a genuinely different target — see render-to-chat.js's own comment.
        result = await renderReadingToChatSpace(store, {
          id: args.id,
          spaceName: args.target_space_name || args.space_name,
        });
        break;
      case 'render_decision_interactive':
        result = await renderDecisionInteractive(store, { id: args.id, channel: args.channel });
        break;
      default:
        return { isError: true, content: [{ type: 'text', text: 'unknown tool: ' + name }] };
    }
  } catch (e) {
    return { isError: true, content: [{ type: 'text', text: (e && e.message) || String(e) }] };
  }
  return { content: [{ type: 'text', text: JSON.stringify(result) }], structuredContent: result };
}
