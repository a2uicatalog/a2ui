// src/adapters/slack.js — the Slack platform descriptor for the adapter
// registry (see registry.js). Wraps the EXISTING routes/command.js,
// routes/interactivity.js, lib/slack-security.js rather than absorbing them
// — this file is thin glue, not a reimplementation.
import { verifySlackSignature } from '../lib/slack-security.js';
import { handleCommand } from '../routes/command.js';
import { handleInteractivity } from '../routes/interactivity.js';
import { slackOwnerKey } from '../storage/index.js';
import { config } from '../config.js';

// Slack routes are public (Slack's servers can't satisfy any auth gate we'd
// put in front of them) — HMAC signature verification against the RAW body
// is the only thing standing between a stranger and these handlers. Must run
// before any JSON/form parsing: Slack signs raw bytes, never a
// re-serialized object. Moved here verbatim from server.js when the
// adapter registry was introduced — see slack-compiler/DESIGN-identity.md
// (ported note in lib/slack-security.js) for why this can't be a generic
// auth middleware the registry imposes on every platform (see
// registry.js's PlatformAdapter contract comment for why registerRoutes
// takes the raw app instead).
async function withSlackSignature(c, next) {
  if (!config.slackSigningSecret || !config.slackBotToken) {
    return c.json({ error: 'Slack surface not configured (SLACK_SIGNING_SECRET/SLACK_BOT_TOKEN unset)' }, 501);
  }
  const rawBody = await c.req.text();
  const ok = await verifySlackSignature(rawBody, c.req.raw, {
    SLACK_SIGNING_SECRET: config.slackSigningSecret,
  });
  if (!ok) return c.text('invalid signature', 401);
  c.set('rawBody', rawBody);
  await next();
}

export const slackAdapter = {
  id: 'slack',
  isConfigured: () => Boolean(config.slackSigningSecret && config.slackBotToken),
  missingConfig: () => [
    !config.slackSigningSecret && 'SLACK_SIGNING_SECRET',
    !config.slackBotToken && 'SLACK_BOT_TOKEN',
  ].filter(Boolean),
  registerRoutes(app) {
    app.post('/slack/command', withSlackSignature, handleCommand);
    app.post('/slack/interactivity', withSlackSignature, handleInteractivity);
  },
  ownerKey: slackOwnerKey,
  ownerKeyFromMcpArgs: (args) => (args.team_id && args.user_id) ? slackOwnerKey(args.team_id, args.user_id) : null,
};
