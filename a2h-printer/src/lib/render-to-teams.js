// src/lib/render-to-teams.js — Teams sibling of render-to-slack.js. Same
// decode -> map -> compile -> post shape; two real differences from Slack:
//
//   1. Teams sends ONE Adaptive Card per message (compilePayload's `card`
//      field), not a flat array of independent blocks — so there's no
//      Slack-style `chartType` lookup needed either, since chart atoms
//      already route through the bucket-D image fallback (teams-mapping.js
//      header explains why TEAMS_CHART_ELEMENTS was deliberately not
//      ported).
//   2. Posting needs a conversation reference (serviceUrl + conversationId)
//      from the INCOMING activity that triggered this, not a bare channel
//      name string — Teams has no equivalent of "#general" you can just
//      target from cold. This mirrors why /slack/command reads
//      team_id/user_id off the signed request rather than accepting them as
//      free-form args.
import { mcpDecode, decodeV1 } from './decode.js';
import { TEAMS_MAPPING } from './teams-mapping.js';
import { compilePayload } from './teams-blocks.js';
import { getConnectorToken } from './teams-auth.js';
import { config } from '../config.js';

// Shared tail: map atom blocks -> compile -> post. Used both by
// renderReadingToTeams (decoded from storage) and by any caller with
// already-built blocks (e.g. weather.js's live data — see
// routes/teams.js's `weather` handler).
export async function postBlocksToTeams(sourceBlocks, { serviceUrl, conversationId } = {}) {
  if (!serviceUrl || !conversationId) {
    return { ok: false, reason: 'serviceUrl and conversationId are required to post into a Teams conversation.' };
  }
  if (!sourceBlocks || !sourceBlocks.length) {
    return { ok: false, reason: 'no renderable blocks.' };
  }

  const skipped = [];
  const atoms = [];
  for (const b of sourceBlocks) {
    const m = TEAMS_MAPPING[b.type];
    if (!m) { skipped.push(b.type); continue; }
    atoms.push({ type: b.type, props: b, target: m.target, bucket: m.bucket });
  }
  if (!atoms.length) {
    return { ok: false, reason: 'none of these atom types compile to a supported Adaptive Card element yet.', skipped };
  }

  const renderConfig = config.renderSigningKey && config.renderBaseUrl
    ? { signingKey: config.renderSigningKey, baseUrl: config.renderBaseUrl }
    : undefined;

  let compiled;
  try { compiled = await compilePayload(atoms, renderConfig); }
  catch (e) { return { ok: false, reason: 'compile failed: ' + ((e && e.message) || e) }; }

  let token;
  try { token = await getConnectorToken(); }
  catch (e) { return { ok: false, reason: 'Connector API auth failed: ' + ((e && e.message) || e) }; }

  const activitiesUrl = `${serviceUrl.replace(/\/+$/, '')}/v3/conversations/${encodeURIComponent(conversationId)}/activities`;
  const resp = await fetch(activitiesUrl, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
    body: JSON.stringify({
      type: 'message',
      attachments: [{ contentType: 'application/vnd.microsoft.card.adaptive', content: compiled.card }],
    }),
  });
  if (!resp.ok) {
    const errText = await resp.text().catch(() => '');
    return { ok: false, reason: `Teams post failed: ${resp.status} ${errText.slice(0, 200)}`,
             blocks_attempted: compiled.blocks.length };
  }
  const out = await resp.json().catch(() => ({}));
  return { ok: true, posted_to: conversationId,
           atoms_compiled: atoms.length, atoms_skipped: skipped,
           degraded: compiled.degraded, truncated: compiled.truncated, activity_id: out.id };
}

// store: caller's storage handle, already scoped to the right owner_key.
// id: reading id, or falsy for "most recent".
// serviceUrl/conversationId: from the incoming Bot Framework Activity —
// required, there is no default the way Slack has slackDefaultChannel.
export async function renderReadingToTeams(store, { id, serviceUrl, conversationId } = {}) {
  const listed = await store.list(null, 100);
  const all = listed.readings || [];
  const row = id ? all.find((r) => r.id === id) : all[0];
  if (!row) {
    return { ok: false, reason: id ? `no reading with id "${id}"` : 'nothing kept yet — save a reading first.' };
  }
  if (!row.payload_p) {
    return { ok: false, reason: 'that reading was saved without its payload, so there is nothing ' +
                                 'portable to render — only a link, which a Teams post cannot use.' };
  }

  let payload;
  try { payload = await mcpDecode(row.payload_p); }
  catch (e) { return { ok: false, reason: 'stored payload did not decode: ' + ((e && e.message) || e) }; }
  const flat = decodeV1(payload);
  const sourceBlocks = (flat && flat.blocks) || [];

  const result = await postBlocksToTeams(sourceBlocks, { serviceUrl, conversationId });
  return { ...result, reading_id: row.id, title: row.title || null };
}
