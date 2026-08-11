// src/adapters/teams.js — the Teams platform descriptor for the adapter
// registry (see registry.js). Wraps the EXISTING routes/teams.js, which
// already does its own config-presence 501 check and per-request JWT
// verification internally (lib/teams-security.js) — unlike Slack's
// raw-body HMAC, Teams' auth needs the parsed body's claims-adjacent
// context, so it can't be a shared pre-route middleware the way Slack's
// withSlackSignature is. registerRoutes just mounts the single Bot
// Framework endpoint; no wrapping needed here.
import { handleTeamsMessage } from '../routes/teams.js';
import { teamsOwnerKey } from '../storage/index.js';
import { config } from '../config.js';

export const teamsAdapter = {
  id: 'teams',
  isConfigured: () => Boolean(config.teamsAppId && config.teamsAppPassword),
  missingConfig: () => [
    !config.teamsAppId && 'TEAMS_APP_ID',
    !config.teamsAppPassword && 'TEAMS_APP_PASSWORD',
  ].filter(Boolean),
  registerRoutes(app) {
    app.post('/api/messages', handleTeamsMessage);
  },
  ownerKey: teamsOwnerKey,
  ownerKeyFromMcpArgs: (args) => (args.tenant_id && args.user_id) ? teamsOwnerKey(args.tenant_id, args.user_id) : null,
};
