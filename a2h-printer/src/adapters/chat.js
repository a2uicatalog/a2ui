// src/adapters/chat.js — the Google Chat platform descriptor for the
// adapter registry (see registry.js). Wraps the EXISTING routes/chat.js,
// which does its own config-presence 501 check and per-request token
// verification internally (lib/chat-security.js) — same shape as
// adapters/teams.js.
import { handleChatEvent } from '../routes/chat.js';
import { chatOwnerKey } from '../storage/index.js';
import { config } from '../config.js';

export const chatAdapter = {
  id: 'chat',
  // Chat additionally requires the render-signing pair, not just
  // CHAT_AUDIENCE — "configured but can't render anything" (Chat has no
  // native compiler) is a worse failure mode than "not configured".
  isConfigured: () => Boolean(config.chatAudiences.length && config.renderSigningKey && config.renderBaseUrl),
  missingConfig: () => [
    !config.chatAudiences.length && 'CHAT_AUDIENCE',
    !config.renderSigningKey && 'RENDER_SIGNING_KEY',
    !config.renderBaseUrl && 'RENDER_BASE_URL',
  ].filter(Boolean),
  registerRoutes(app) {
    app.post('/chat', handleChatEvent);
  },
  ownerKey: chatOwnerKey,
  ownerKeyFromMcpArgs: (args) => (args.space_name && args.user_name) ? chatOwnerKey(args.space_name, args.user_name) : null,
};
