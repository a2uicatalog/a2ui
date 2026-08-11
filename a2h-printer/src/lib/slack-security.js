// src/lib/slack-security.js — Slack request signature verification, shared by
// every Slack route. Ported verbatim from a2ui-private/mcp-worker's
// slack-security.js — this file has zero Cloudflare dependency (pure Web
// Crypto), only the safeEqual import path changed.

import { safeEqual } from './crypto-utils.js';

// https://docs.slack.dev/authentication/verifying-requests-from-slack — the
// documented v0 scheme: HMAC-SHA256 over "v0:{timestamp}:{raw body}", hex-
// encoded, prefixed "v0=". MUST run against the RAW body text, before any
// JSON.parse or form-decode — Slack signs bytes, not a re-serialized object,
// so parsing first and re-stringifying would silently break every signature.
export async function verifySlackSignature(rawBody, request, env) {
  if (!env || !env.SLACK_SIGNING_SECRET) return false;
  const ts = request.headers.get('X-Slack-Request-Timestamp');
  const sig = request.headers.get('X-Slack-Signature');
  if (!ts || !sig) return false;

  // Replay protection: Slack recommends rejecting anything more than 5
  // minutes old, since request forgery only needs a plausible-looking
  // (timestamp, signature) pair, not a live secret, once one is captured.
  const ageSeconds = Math.abs(Date.now() / 1000 - Number(ts));
  if (!Number.isFinite(ageSeconds) || ageSeconds > 300) return false;

  const base = `v0:${ts}:${rawBody}`;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(env.SLACK_SIGNING_SECRET),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(base));
  const computed = 'v0=' + [...new Uint8Array(mac)]
    .map((b) => b.toString(16).padStart(2, '0')).join('');

  // Timing-safe — the same primitive checkMcpAuth already uses for the
  // service-key comparison, not a second hand-rolled one.
  return safeEqual(computed, sig);
}
