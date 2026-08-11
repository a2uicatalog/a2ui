// POST /chat — Google Chat's single webhook endpoint. Scoped to
// SYNCHRONOUS webhook-reply for this phase (list/show/help/weather) —
// proactive posting (an agent pushing content into a space it isn't
// currently being messaged in) is a separate concern, see lib/chat-auth.js
// and /mcp's render_reading_to_chat tool.
//
// Structurally closest to routes/command.js: the reply IS the returned
// Hono response body (synchronous), not a side-effecting POST the way
// Teams' replyText is. Envelope parsing + Chat-specific reply shaping
// only — the actual help|whoami|list|show|weather business logic lives
// once, in lib/command-handler.js, shared with routes/command.js and
// routes/teams.js.
import { verifyChatRequest } from '../lib/chat-security.js';
import { getStore, chatOwnerKey } from '../storage/index.js';
import { renderReadingToChat, postBlocksToChat } from '../lib/render-to-chat.js';
import { fetchWeatherBlocks } from '../lib/weather.js';
import { runCommand } from '../lib/command-handler.js';
import { config } from '../config.js';

export async function handleChatEvent(c) {
  // Chat additionally needs the render-signing pair to be USEFUL, not just
  // CHAT_AUDIENCE to be configured — Chat has no native compiler, so every
  // reply needs the image-render fallback to display anything at all. See
  // adapters/chat.js's isConfigured(), which checks all three together.
  if (!config.chatAudiences.length || !config.renderSigningKey || !config.renderBaseUrl) {
    return c.json({
      text: 'Chat surface not configured (CHAT_AUDIENCE + RENDER_SIGNING_KEY + RENDER_BASE_URL are ' +
            'all required — Chat has no native compiler, see README).',
    }, 501);
  }

  try {
    await verifyChatRequest((name) => c.req.header(name), {
      audiences: config.chatAudiences,
      trustCloudRunIam: config.chatTrustCloudRunIam,
    });
  } catch (e) {
    return c.json({ error: (e && e.message) || String(e) }, 403);
  }

  const event = await c.req.json().catch(() => ({}));
  const spaceName = event.space && event.space.name;
  const userName = event.user && event.user.name;
  if (!spaceName || !userName) {
    // Nothing safe to key storage on — reply with a plain message rather
    // than posting anything or guessing an identity.
    return c.json({ text: 'Could not identify this Chat message.' });
  }

  // Chat delivers the text with the app's own @mention already stripped
  // into argumentText — unlike Slack's slash-command text (never contains
  // the app name) or Teams' <at> markup (routes/teams.js strips it),
  // there's nothing to strip here.
  const text = ((event.message && event.message.argumentText) || '').trim();

  let replyPayload = { text: '' };
  const reply = (msg) => { replyPayload = { text: msg }; };

  await runCommand({
    text,
    ownerKey: chatOwnerKey(spaceName, userName),
    getStore,
    reply,
    helpText: () => 'Usage: "list" to see your saved readings, "show <id>" to post one here, "weather <city>" for a live forecast card.',
    unknownText: () => 'Unknown command. Usage: "list", "show <id>", "weather <city>".',
    // Debug affordance, matching /a2ui whoami on Slack/Teams — the space
    // and user resource names aren't secrets, and they're exactly what
    // /mcp needs to target a save against this same identity for testing.
    whoamiText: () => `space: ${spaceName}\nuser: ${userName}`,
    listLineFor: (r) => `- ${r.id} — ${r.title || '(untitled)'}`,
    renderReading: async (store, { id }) => {
      const result = await renderReadingToChat(store, { id });
      if (result.ok) replyPayload = result.card;
      else reply(`Could not post: ${result.reason}`);
    },
    weatherUsageText: () => 'Usage: "weather <city>"',
    fetchWeather: fetchWeatherBlocks,
    postWeather: async (store, weather) => {
      const result = await postBlocksToChat(weather.blocks, { title: `Weather — ${weather.location}` });
      if (result.ok) replyPayload = result.card;
      else reply(`Could not post: ${result.reason}`);
    },
  });

  return c.json(replyPayload);
}
