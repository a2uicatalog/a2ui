// src/lib/decision-nav.js — interactive click-through navigation for the
// decision_tree atom (an actual walk, one Slack message updated in place per
// click — NOT the static render.png escape hatch used elsewhere in this
// package for atoms with no native Slack shape).
//
// decision_tree's REAL data shape (confirmed against the renderer,
// a2ui-catalogue/renderers/web_article.py's _render_decision_tree —
// atoms/schema.yaml documents a DIFFERENT nested {text, children:[...]}
// shape that the renderer does not actually accept): a FLAT node list keyed
// by `id`, edges expressed as `children: [{label, next: <id>}]`, `label`
// (not `text`) as the display field, `type` one of question|action|leaf.
// A root is any node whose id never appears as another node's child.next —
// same convention the renderer itself uses to decide what to draw first.
import { mcpDecode, decodeV1 } from './decode.js';

function findRoot(nodes) {
  const childIds = new Set();
  for (const n of nodes) {
    for (const c of n.children || []) {
      if (c.next) childIds.add(c.next);
    }
  }
  return nodes.find((n) => !childIds.has(n.id)) || nodes[0];
}

/**
 * Loads a saved reading's decision_tree atom. Throws with a message safe to
 * show the user directly (no internal detail) — every caller here is on a
 * Slack-facing path (initial post or a button click), never a silent
 * background job.
 */
export async function loadDecisionTree(store, readingId) {
  const listed = await store.list(null, 100);
  const all = listed.readings || [];
  const row = readingId ? all.find((r) => r.id === readingId) : all[0];
  if (!row) throw new Error(readingId ? `no reading with id "${readingId}"` : 'nothing saved yet — save a reading first.');
  if (!row.payload_p) throw new Error('that reading has no payload to walk.');
  const payload = await mcpDecode(row.payload_p);
  const flat = decodeV1(payload);
  const atom = (flat.blocks || []).find((b) => b.type === 'decision_tree');
  if (!atom || !Array.isArray(atom.nodes) || !atom.nodes.length) {
    throw new Error('that reading has no decision_tree atom to walk.');
  }
  return { readingId: row.id, title: row.title || atom.title || null, nodes: atom.nodes };
}

export function rootNodeId(nodes) {
  return findRoot(nodes).id;
}

const TYPE_EMOJI = { question: '🔷', action: '🟠', leaf: '🟢' };

// Slack limits: 5 buttons/actions-block is comfortable (not a hard Slack
// cap — 25 is — but keeps a demo tree readable rather than a wall of
// buttons); action_id 255 chars, so `${prefix}:${readingId}:${index}` is
// nowhere close. Value only carries {nodeId} — the tree itself is looked up
// fresh from storage on every click via the readingId in action_id, never
// round-tripped through the button (keeps clicks small and lets the same
// tree be re-walked from any starting point without re-encoding it).
export function buildStepBlocks(readingId, nodes, nodeId, title) {
  const node = nodes.find((n) => n.id === nodeId) || findRoot(nodes);
  const emoji = TYPE_EMOJI[node.type] || '▪️';
  const blocks = [];
  if (title) blocks.push({ type: 'header', text: { type: 'plain_text', text: title.slice(0, 150), emoji: true } });
  blocks.push({ type: 'section', text: { type: 'mrkdwn', text: `${emoji} *${node.label}*` } });

  const children = (node.children || []).filter((c) => c.next);
  if (children.length) {
    blocks.push({
      type: 'actions',
      elements: children.slice(0, 5).map((c, i) => ({
        type: 'button',
        text: { type: 'plain_text', text: String(c.label || '(choice)').slice(0, 75), emoji: true },
        action_id: `a2ui_decision_nav:${readingId}:${i}`,
        value: JSON.stringify({ nodeId: c.next }),
      })),
    });
  } else {
    blocks.push({ type: 'context', elements: [{ type: 'mrkdwn', text: '_End of path — no further steps._' }] });
  }
  return blocks;
}
