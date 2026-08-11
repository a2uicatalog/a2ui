// src/lib/render-to-chat.js — mirrors render-to-slack.js's two-export shape
// (renderReadingToChat/postBlocksToChat) but is ALWAYS-IMAGE: no mapping
// table, no bucket ladder — confirmed Chat has no native atom candidates
// (cardsV2's widget set is fixed), so every atom becomes one
// signRenderUrl(...) call wrapped in a cardsV2 `image` widget. See
// /home/curtis/.claude/plans/zany-petting-cray.md's Google Chat adapter
// section.
//
// postBlocksToChat/renderReadingToChat do NOT post anywhere themselves —
// Chat's synchronous webhook-reply mode (routes/chat.js) returns the built
// card AS the HTTP response body. renderReadingToChatSpace below (added for
// proactive posting) is the one that actually calls chat-auth.js's
// postToChatSpace — kept as a separate function rather than folding posting
// into renderReadingToChat, so the synchronous webhook-reply path never
// pays for or depends on the outbound-credential machinery it doesn't need.
import { mcpDecode, decodeV1 } from './decode.js';
import { signRenderUrl } from './crypto-utils.js';
import { postToChatSpace } from './chat-auth.js';
import { config } from '../config.js';

// Builds a cardsV2 payload from arbitrary A2UI blocks. store/id: same
// contract as renderReadingToSlack/Teams's channel argument is dropped —
// Chat's reply target is implicit (the space that sent the event), not a
// caller-supplied parameter.
export async function postBlocksToChat(sourceBlocks, { title } = {}) {
  if (!config.renderSigningKey || !config.renderBaseUrl) {
    return {
      ok: false,
      reason: 'RENDER_SIGNING_KEY/RENDER_BASE_URL are not set — Chat has no native compiler, ' +
              'every atom needs the image-render fallback to display anything.',
    };
  }
  if (!sourceBlocks || !sourceBlocks.length) {
    return { ok: false, reason: 'no renderable blocks.' };
  }

  const renderConfig = { signingKey: config.renderSigningKey, baseUrl: config.renderBaseUrl };
  const widgets = [];
  for (const b of sourceBlocks) {
    let url;
    try {
      url = await signRenderUrl(b.type, b, renderConfig);
    } catch (e) {
      return { ok: false, reason: `render signing failed for "${b.type}": ` + ((e && e.message) || e) };
    }
    widgets.push({ image: { imageUrl: url, altText: b.type } });
  }

  const card = {
    cardsV2: [{
      cardId: 'a2ui',
      card: {
        ...(title ? { header: { title } } : {}),
        sections: [{ widgets }],
      },
    }],
  };
  // title echoed back for MCP-caller parity with postBlocksToSlack/Teams'
  // own return shape, even though it's also baked into the card itself.
  return { ok: true, card, title: title || null };
}

export async function renderReadingToChat(store, { id } = {}) {
  const listed = await store.list(null, 100);
  const all = listed.readings || [];
  const row = id ? all.find((r) => r.id === id) : all[0];
  if (!row) {
    return { ok: false, reason: id ? `no reading with id "${id}"` : 'nothing kept yet — save a reading first.' };
  }
  if (!row.payload_p) {
    return {
      ok: false,
      reason: 'that reading was saved without its payload, so there is nothing portable to render — ' +
              'only a link, which a Chat card cannot use.',
    };
  }

  let payload;
  try {
    payload = await mcpDecode(row.payload_p);
  } catch (e) {
    return { ok: false, reason: 'stored payload did not decode: ' + ((e && e.message) || e) };
  }
  const flat = decodeV1(payload);
  const sourceBlocks = (flat && flat.blocks) || [];

  const result = await postBlocksToChat(sourceBlocks, { title: row.title });
  return { ...result, reading_id: row.id };
}

// Proactive posting — an agent pushing a saved reading into a Chat space it
// isn't currently being messaged in (via /mcp's render_reading_to_chat),
// mirroring what render_reading_to_slack/render_reading_to_teams already
// let an agent do. Unlike renderReadingToChat above (which only BUILDS a
// card, for the synchronous webhook-reply case), this one also POSTS it,
// via chat-auth.js's service-identity credential.
//
// spaceName: "spaces/AAAAxxxxxxx" — the TARGET space, supplied explicitly
// by the caller. There's no inbound webhook here to infer it from (same
// reasoning as render-to-slack.js's channel parameter), and it need not be
// the same space the reading's OWNER identity belongs to — an agent may
// save a reading against one identity and push it into a different space
// it has access to.
export async function renderReadingToChatSpace(store, { id, spaceName } = {}) {
  if (!spaceName) {
    return { ok: false, reason: 'spaceName (e.g. "spaces/AAAAxxxxxxx") is required to post proactively.' };
  }
  const built = await renderReadingToChat(store, { id });
  if (!built.ok) return built;
  const posted = await postToChatSpace(spaceName, built.card);
  if (!posted.ok) return { ok: false, reason: posted.reason, reading_id: built.reading_id };
  return { ok: true, posted_to: spaceName, reading_id: built.reading_id, title: built.title };
}
