// src/lib/slack-interactivity.js — handles POST /slack/interactivity payloads.
// Ported from a2ui-private/mcp-worker's slack-interactivity.js with three
// changes:
//   1. Signature verification moved to server.js's shared middleware (both
//      /slack/command and /slack/interactivity go through it) rather than
//      being called again here.
//   2. Reads config.slackBotToken instead of a Workers `env` binding.
//   3. The 212Trading bridge integration (recordTradingDecision) was cut —
//      that's Curtis's own private trading-bot wiring, not something a
//      generic self-hosted Slack Surface should ship with. The generic
//      approve/deny HITL gate (recordDecision, `a2ui_decision:*`) stays.
//
// GENERIC ON PURPOSE (unchanged from the source): this does not hardcode any
// specific atom or button. It reads {atomType, props, title} out of the
// CLICKED BUTTON's own `value` and compiles+opens whatever it's given.
//
// The modal-open path (views.open, needs a live trigger_id) stays
// synchronous/inline — a trigger_id can't be deferred to a background task,
// unlike response_url updates below, which ack first per plan decision #2a.

import { compileInput, buildModalView } from './slack-inputs.js';
import { config } from '../config.js';
import { getStore, slackOwnerKey } from '../storage/index.js';
import { loadDecisionTree, buildStepBlocks } from './decision-nav.js';

const VIEWS_OPEN_URL = 'https://slack.com/api/views.open';

async function openView(triggerId, view) {
  const resp = await fetch(VIEWS_OPEN_URL, {
    method: 'POST',
    headers: {
      'content-type': 'application/json; charset=utf-8',
      authorization: `Bearer ${config.slackBotToken}`,
    },
    body: JSON.stringify({ trigger_id: triggerId, view }),
  });
  const body = await resp.json();
  if (!body.ok) throw new Error(`views.open failed: ${body.error || 'unknown error'}`);
  return body;
}

// Interactivity payloads arrive as application/x-www-form-urlencoded with a
// single `payload` field holding URL-encoded JSON — a DIFFERENT shape from
// /slack/command's flat form fields, and from message-shortcut /
// global-shortcut payloads, which this route does not yet handle
// (block_actions only — the concrete case a button click needs).
//
// Returns the ack body/status the route handler should send back to Slack.
// The caller (routes/interactivity.js) is responsible for actually sending
// it within the 3s deadline — this function does the same, but keeps the
// HTTP framing out of the ported logic.
export async function processInteractivity(rawBody) {
  const params = new URLSearchParams(rawBody);
  let payload;
  try {
    payload = JSON.parse(params.get('payload') || '{}');
  } catch (e) {
    return; // malformed — ack anyway, per Slack's own guidance: never leave the button spinning
  }

  if (payload.type !== 'block_actions') return;

  const actions = payload.actions || [];

  const openAction = actions.find((a) => a.action_id && a.action_id.startsWith('a2ui_open_modal:'));
  if (openAction && payload.trigger_id) {
    let spec;
    try {
      spec = JSON.parse(openAction.value || '{}');
    } catch (e) {
      return; // malformed button value — nothing safe to open, ack and stop
    }
    if (!spec.atomType) return;

    try {
      const { blocks } = compileInput(spec.atomType, spec.props || {});
      const view = buildModalView({
        title: spec.title || spec.atomType,
        blocks,
        callbackId: `a2ui:${spec.atomType}`,
      });
      await openView(payload.trigger_id, view);
    } catch (e) {
      // views.open failing (or compileInput throwing on an atom this file
      // doesn't know) is not the CALLER's fault to see as an HTTP error —
      // Slack already has the ack it needs. Logged for our own
      // observability, never surfaced back to the click as a broken button.
      console.error('slack-interactivity: could not open modal', e && e.message);
    }
    return;
  }

  const decisionAction = actions.find((a) => a.action_id && a.action_id.startsWith('a2ui_decision:'));
  if (decisionAction && payload.response_url) {
    // Ack-first per plan decision #2a: response_url updates aren't
    // trigger_id-bound and have their own ~30min validity window, so unlike
    // the modal-open path above, this doesn't need to complete before the
    // interactivity POST is acked. The caller sends the ack; this runs after,
    // fire-and-forget (safe on a long-lived Node process, unlike a Worker
    // isolate without ctx.waitUntil — see file header).
    recordDecision(decisionAction, payload).catch((e) =>
      console.error('slack-interactivity: recordDecision failed', e && e.message));
  }

  // Click-through decision_tree walk — one message updated in place per
  // click, distinct from recordDecision's one-shot approve/deny gate above.
  // action_id: `a2ui_decision_nav:<readingId>:<index>` (index only for
  // per-button action_id uniqueness, unused past parsing); value carries
  // just {nodeId} — the tree itself is re-loaded from storage on every
  // click rather than round-tripped through the button.
  const navAction = actions.find((a) => a.action_id && a.action_id.startsWith('a2ui_decision_nav:'));
  if (navAction && payload.response_url) {
    navigateDecisionTree(navAction, payload).catch((e) =>
      console.error('slack-interactivity: navigateDecisionTree failed', e && e.message));
  }
}

async function navigateDecisionTree(action, payload) {
  const readingId = action.action_id.slice('a2ui_decision_nav:'.length).split(':')[0];
  let nodeId;
  try {
    nodeId = JSON.parse(action.value || '{}').nodeId;
  } catch (e) {
    return; // malformed value — nothing safe to navigate to
  }

  const team = payload.team || {};
  const user = payload.user || {};
  if (!team.id || !user.id) return;

  let store;
  try {
    store = getStore(slackOwnerKey(team.id, user.id));
  } catch (e) {
    console.error('slack-interactivity: storage unavailable for decision nav', e && e.message);
    return;
  }

  let tree;
  try {
    tree = await loadDecisionTree(store, readingId);
  } catch (e) {
    // Reading gone or malformed — tell the clicker rather than leaving a
    // dead button with no feedback at all.
    await fetch(payload.response_url, {
      method: 'POST',
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ response_type: 'ephemeral', text: `Could not continue: ${e.message}` }),
    });
    return;
  }

  const blocks = buildStepBlocks(tree.readingId, tree.nodes, nodeId, tree.title);
  const resp = await fetch(payload.response_url, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ replace_original: true, text: tree.title || 'Decision tree', blocks }),
  });
  if (!resp.ok) console.error('slack-interactivity: decision nav response_url update failed', resp.status);
}

// Human-in-the-loop approve/deny gate. `a2ui_decision:<slug>` is a
// convention on the action_id, not a dedicated atom — any Bucket A `actions`
// button opts in by using this prefix.
//
// Uses `response_url` (present on every block_actions payload, scoped to
// THIS message, no bot token) rather than `chat.update` — needs zero
// additional Slack scopes.
async function recordDecision(action, payload) {
  const slug = action.action_id.slice('a2ui_decision:'.length);
  let spec = {};
  try {
    spec = JSON.parse(action.value || '{}');
  } catch (e) {
    // malformed value — still show a decision was made, just without the label
  }
  const label = spec.label || (action.text && action.text.text) || 'Request';
  const user = payload.user || {};
  const who = user.username || user.name || user.id || 'someone';
  const icon = slug === 'approve' ? '✅' : slug === 'deny' ? '❌' : '☑️';
  const text = `${icon} *${label}*\n${slug} by ${user.id ? `<@${user.id}>` : who}`;
  const resp = await fetch(payload.response_url, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify({
      replace_original: true,
      text: `${icon} ${label} — ${slug} by ${who}`,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text } }],
    }),
  });
  if (!resp.ok) console.error('slack-interactivity: response_url update failed', resp.status);
}
