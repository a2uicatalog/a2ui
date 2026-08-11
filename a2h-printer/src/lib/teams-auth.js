// src/lib/teams-auth.js — outbound auth for the Bot Framework Connector API
// (the API used to actually POST a card back into a Teams conversation).
// OAuth2 client-credentials flow, cached with expiry-aware refresh — the
// Teams sibling of Slack's simple static Bearer bot token (config.slackBotToken);
// there's no equivalent static token here, every outbound call needs a
// freshly-scoped access token.
//
// TENANT/AUTHORITY — VERIFY AGAINST CURRENT MICROSOFT DOCS BEFORE RELYING ON
// THIS IN PRODUCTION: the default below (`botframework.com`) is the
// documented authority for a MultiTenant Azure Bot app registration (the
// common case for a Teams bot). A SingleTenant app registration instead
// needs its own home tenant ID here. This is exactly the kind of detail
// that's easy to get subtly wrong from memory and that changes on
// Microsoft's side without this package's knowledge — a wrong value fails
// LOUD (token request rejected) rather than silently, so it's safe to try
// and correct, not a silent security gap, but confirm which app type you
// registered and set TEAMS_AUTH_TENANT accordingly if it's not MultiTenant.
import { config } from '../config.js';

const TOKEN_SCOPE = 'https://api.botframework.com/.default';

let cached = null; // { token, expiresAt }

function tokenUrl() {
  return `https://login.microsoftonline.com/${config.teamsAuthTenant}/oauth2/v2.0/token`;
}

export async function getConnectorToken() {
  const now = Date.now();
  // Refresh a minute early — never let an in-flight request race an
  // about-to-expire token.
  if (cached && cached.expiresAt - 60_000 > now) return cached.token;

  const body = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: config.teamsAppId,
    client_secret: config.teamsAppPassword,
    scope: TOKEN_SCOPE,
  });
  const resp = await fetch(tokenUrl(), {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
  const json = await resp.json();
  if (!resp.ok || !json.access_token) {
    throw new Error(`Connector API token request failed: ${json.error_description || json.error || resp.status}`);
  }
  cached = { token: json.access_token, expiresAt: now + json.expires_in * 1000 };
  return cached.token;
}
