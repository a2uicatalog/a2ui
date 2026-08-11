// src/lib/render-to-slack.js — extracted from mcp-worker/src/tools.js's
// mcpRenderReadingToSlack (~line 2278-2388). Two things dropped versus the
// source, both per plan decision #1 (no separate reader-account system in
// v1): the store.linkList() lookup ("which Slack account is linked to this
// reader") and the OAuth __IDENTITY__ gate. Storage here is ALREADY keyed
// directly on the Slack identity (owner_key = slack:{team_id}:{user_id}),
// so there's no separate account to look up or link — the caller supplies
// the owning store directly.
//
// Also dropped: the RENDER_SIGNING_KEY/RENDER_BASE_URL signed-image-render
// fallback (Cloudflare-adjacent infra, out of scope for this package).
import { mcpDecode, decodeV1 } from './decode.js';
import { SLACK_MAPPING, SLACK_CHART_TYPES } from './slack-mapping.js';
import { compilePayload } from './slack-blocks.js';
import { config } from '../config.js';

const POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage';

// Shared tail: map atom blocks -> compile -> post. Used both by
// renderReadingToSlack (decoded from storage) and by any caller with
// already-built blocks (e.g. weather.js's live data, which was never
// stored/decoded at all — see routes/command.js's `weather` handler).
export async function postBlocksToSlack(sourceBlocks, { channel, title } = {}) {
  if (!sourceBlocks || !sourceBlocks.length) {
    return { ok: false, reason: 'no renderable blocks.' };
  }

  const skipped = [];
  const atoms = [];
  for (const b of sourceBlocks) {
    const m = SLACK_MAPPING[b.type];
    if (!m) { skipped.push(b.type); continue; }
    atoms.push({ type: b.type, props: b, target: m.target, bucket: m.bucket,
                 chartType: SLACK_CHART_TYPES[b.type] });
  }
  if (!atoms.length) {
    return { ok: false, reason: 'none of these atom types compile to a supported Slack block yet.', skipped };
  }

  // renderConfig enables the D-bucket image fallback (atoms with no native
  // Slack block) by reusing cloud-run-renderer's already-live, already-
  // signed /render.png — see slack-blocks.js's eImageRender/signRenderUrl.
  // undefined (not a partial object) when either half is unset, matching
  // compileAtom's own "omit entirely if unused" contract.
  const renderConfig = config.renderSigningKey && config.renderBaseUrl
    ? { signingKey: config.renderSigningKey, baseUrl: config.renderBaseUrl }
    : undefined;

  let compiled;
  try { compiled = await compilePayload(atoms, renderConfig); }
  catch (e) { return { ok: false, reason: 'compile failed: ' + ((e && e.message) || e) }; }

  const target = channel || config.slackDefaultChannel;
  const resp = await fetch(POST_MESSAGE_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8',
               authorization: 'Bearer ' + config.slackBotToken },
    body: JSON.stringify({ channel: target, text: title || 'A2UI reading', blocks: compiled.blocks }),
  });
  const out = await resp.json();
  if (!out.ok) {
    return { ok: false, reason: 'Slack post failed: ' + (out.error || 'unknown'),
             blocks_attempted: compiled.blocks.length };
  }
  return { ok: true, posted_to: target, title: title || null,
           atoms_compiled: atoms.length, atoms_skipped: skipped,
           degraded: compiled.degraded, truncated: compiled.truncated, slack_ts: out.ts };
}

// store: the caller's storage handle (see storage/index.js), already scoped
// to the right owner_key. id: reading id, or falsy for "most recent".
// channel: Slack channel to post to, defaults to config.slackDefaultChannel.
export async function renderReadingToSlack(store, { id, channel } = {}) {
  const listed = await store.list(null, 100);
  const all = listed.readings || [];
  const row = id ? all.find((r) => r.id === id) : all[0];
  if (!row) {
    return { ok: false, reason: id ? `no reading with id "${id}"` : 'nothing kept yet — save a reading first.' };
  }
  if (!row.payload_p) {
    return { ok: false, reason: 'that reading was saved without its payload, so there is nothing ' +
                                 'portable to render — only a link, which a Slack post cannot use.' };
  }

  let payload;
  try { payload = await mcpDecode(row.payload_p); }
  catch (e) { return { ok: false, reason: 'stored payload did not decode: ' + ((e && e.message) || e) }; }
  const flat = decodeV1(payload);
  const sourceBlocks = (flat && flat.blocks) || [];

  const result = await postBlocksToSlack(sourceBlocks, { channel, title: row.title });
  return { ...result, reading_id: row.id };
}
