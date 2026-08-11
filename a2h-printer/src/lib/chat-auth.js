// src/lib/chat-auth.js — OUTBOUND auth for proactive Chat posting: an agent
// pushing content into a space it isn't currently being messaged in (via
// /mcp's render_reading_to_chat), mirroring what render_reading_to_slack/
// render_reading_to_teams already let an agent do for Slack/Teams. This is
// the one place Chat's outbound auth is genuinely a THIRD shape: Slack is a
// static bot token (config.slackBotToken); Teams is an OAuth2 client-
// credentials flow (teams-auth.js); Chat is a service identity.
//
// Uses google-auth-library's GoogleAuth (Application Default Credentials
// discovery), NOT a hand-rolled OAuth2 flow — its own request() method
// handles token acquisition/refresh/auth-header attachment automatically.
// This is a materially SIMPLER shape than teams-auth.js's cached-token
// flow needed, precisely because ADC does that work for us.
//
// THE KEY CONSTRAINT (get this wrong and every post opaquely 403s): Google
// Chat's app-authenticated spaces.messages.create requires the caller to
// be the SPECIFIC service account registered as this Chat app's identity
// in the Chat API configuration — not just any GCP principal with API
// access. On Cloud Run, zero-key-file ADC only works if the service was
// deployed with --service-account=<that specific SA> (deploy.sh's
// CHAT_SERVICE_ACCOUNT var does this). GOOGLE_SERVICE_ACCOUNT_KEY (a raw
// JSON key, for non-GCP hosts with no attachable identity) or
// GOOGLE_APPLICATION_CREDENTIALS (a key FILE path, ADC's own standard env
// var) are the fallback.
import { GoogleAuth } from 'google-auth-library';
import { config } from '../config.js';

const CHAT_API_BASE = 'https://chat.googleapis.com/v1';
const CHAT_SCOPES = ['https://www.googleapis.com/auth/chat.bot'];

let authClient = null;
function getAuth() {
  return authClient ??= new GoogleAuth({
    // undefined (not a partial object) when unset, so ADC's own discovery
    // chain runs unmodified — GOOGLE_APPLICATION_CREDENTIALS (a file path)
    // if set, then the Cloud Run metadata server, in that order. Explicit
    // JSON credentials only override that chain when GOOGLE_SERVICE_ACCOUNT_KEY
    // is actually set.
    credentials: config.chatServiceAccountKey ? JSON.parse(config.chatServiceAccountKey) : undefined,
    scopes: CHAT_SCOPES,
  });
}

// Named, distinguishable failure reasons — Chat's outbound path has several
// opaque-by-default HTTP failures an agent calling render_reading_to_chat
// needs told apart, not collapsed into one generic error (unlike Slack/
// Teams, where outbound failures are mostly self-explanatory "bad token" or
// "channel not found"). Google's API error shape is the standard
// google.rpc.Status envelope: { error: { code, message, status } }.
function describeChatApiError(e) {
  const status = e && e.response && e.response.status;
  const body = e && e.response && e.response.data;
  const apiMessage = (body && body.error && body.error.message) || (e && e.message) || String(e);

  if (status === 403) {
    return 'the deploying identity is not authorized to post as this Chat app — confirm the ' +
           'attached service account (CHAT_SERVICE_ACCOUNT at deploy time, or ' +
           'GOOGLE_SERVICE_ACCOUNT_KEY) is the SAME service account registered as this Chat ' +
           `app's identity in the Chat API configuration, not just any GCP principal. (${apiMessage})`;
  }
  if (status === 404) {
    return `space not found — check the space resource name (e.g. "spaces/AAAAxxxxxxx"). (${apiMessage})`;
  }
  if (status === 401) {
    return 'credential was not accepted — confirm CHAT_SERVICE_ACCOUNT / ' +
           `GOOGLE_SERVICE_ACCOUNT_KEY / GOOGLE_APPLICATION_CREDENTIALS is set correctly. (${apiMessage})`;
  }
  return `Chat API request failed${status ? ` (HTTP ${status})` : ''}: ${apiMessage}`;
}

// Posts a message (text or cardsV2) into an existing space. spaceName:
// "spaces/AAAAxxxxxxx" (Chat's own resource-name format, same value
// storage/index.js's chatOwnerKey uses). messageBody: a plain
// { text } or { cardsV2 } object — same shape render-to-chat.js's
// postBlocksToChat already builds for the synchronous webhook-reply path.
export async function postToChatSpace(spaceName, messageBody) {
  try {
    const resp = await getAuth().request({
      url: `${CHAT_API_BASE}/${spaceName}/messages`,
      method: 'POST',
      data: messageBody,
    });
    return { ok: true, message: resp.data };
  } catch (e) {
    return { ok: false, reason: describeChatApiError(e) };
  }
}

// Boot-time self-check — a dry-run token fetch (never a real API call), so
// a misattributed service account surfaces as a clear log line at DEPLOY
// time rather than silently waiting for an agent's first real post to
// discover it. Logged, never thrown: this must not crash a deployment that
// only uses Chat's inbound webhook-reply path (phase 7) and has no
// outbound credential configured at all — that's a valid, common shape,
// not a misconfiguration.
export async function selfCheckChatAuth() {
  if (!config.chatAudiences.length) return; // Chat surface not enabled at all
  try {
    const client = await getAuth().getClient();
    await client.getAccessToken();
    console.log('[chat-auth] outbound credential resolved OK (proactive posting via /mcp render_reading_to_chat is usable)');
  } catch (e) {
    console.warn('[chat-auth] WARNING: could not resolve an outbound credential — ' +
      'render_reading_to_chat will fail until this is fixed. ' +
      'Set CHAT_SERVICE_ACCOUNT at deploy time (Cloud Run) or GOOGLE_SERVICE_ACCOUNT_KEY ' +
      `(other hosts). (${(e && e.message) || e})`);
  }
}
