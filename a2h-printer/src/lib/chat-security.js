// src/lib/chat-security.js — inbound Google Chat request verification.
//
// Ported from cloud-run-renderer/server.py's _require_chat_caller (read
// line-for-line against the live file, not summarized from the blog post
// that describes it) — see
// /home/curtis/.claude/plans/zany-petting-cray.md for the full port
// rationale. Uses google-auth-library rather than jose (unlike
// teams-security.js) because Chat has TWO genuinely different verification
// paths and google-auth-library already implements both, with a track
// record — it's what server.py itself uses in production. jose would mean
// hand-building the x509 cert-fetch/cache path from scratch with zero JS
// precedent anywhere in the estate, on a security-critical check.
import { OAuth2Client } from 'google-auth-library';
import { config } from '../config.js';

// Exact match to cloud-run-renderer/server.py's constants — verified
// against the live source, not re-derived from memory.
const CHAT_ISSUER = 'chat@system.gserviceaccount.com';
const CHAT_CERTS_URL = 'https://www.googleapis.com/service_accounts/v1/metadata/x509/' + CHAT_ISSUER;
const MIN_REAL_SIGNATURE_CHARS = 100; // server.py's _MIN_REAL_SIGNATURE_CHARS

const oauth2Client = new OAuth2Client();

// Chat's x509 certs endpoint returns a plain {kid: pemCert, ...} object —
// NOT JWKS-shaped — which happens to be EXACTLY the `certs` shape
// OAuth2Client.verifySignedJwtWithCertsAsync expects directly (confirmed by
// reading google-auth-library's own source: certs[envelope.kid] is used as
// the PEM cert as-is), so no reshaping is needed, only fetching + caching.
let x509CertsCache = null; // { certs, fetchedAt }
const X509_CACHE_TTL_MS = 60 * 60 * 1000;

async function getX509Certs(forceRefresh) {
  if (!forceRefresh && x509CertsCache && Date.now() - x509CertsCache.fetchedAt < X509_CACHE_TTL_MS) {
    return x509CertsCache.certs;
  }
  const resp = await fetch(CHAT_CERTS_URL);
  if (!resp.ok) throw new Error(`could not fetch Chat x509 certs: HTTP ${resp.status}`);
  const certs = await resp.json();
  x509CertsCache = { certs, fetchedAt: Date.now() };
  return certs;
}

function decodeJwtPayloadUnverified(bearer) {
  const parts = bearer.split('.');
  if (parts.length !== 3) throw new Error('malformed bearer token');
  const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  return JSON.parse(Buffer.from(b64, 'base64').toString('utf8'));
}

// A ~858-char real RS256 JWT arrives at an IAM-gated Cloud Run service with
// a 34-char signature segment where a real one is 342 — Cloud Run verifies
// the token and then REPLACES its signature before forwarding, so the
// receiving service cannot replay it. Measured live against
// cloud-run-renderer (2026-08-01); this threshold is server.py's own,
// carried over verbatim, not guessed.
function hasRealSignature(bearer) {
  const parts = bearer.split('.');
  return parts.length === 3 && parts[2].length >= MIN_REAL_SIGNATURE_CHARS;
}

// Bearer can arrive on Authorization OR X-Serverless-Authorization (Cloud
// Run's own second convention for the header it authenticated from), and
// the scheme arrives LOWERCASED ('bearer ') after Cloud Run's own rewrite —
// a naive `startsWith('Bearer ')` silently rejects every real request.
// Both facts measured live against cloud-run-renderer, 2026-08-01.
export function extractBearer(getHeader) {
  for (const name of ['Authorization', 'X-Serverless-Authorization']) {
    const value = getHeader(name) || '';
    if (value.slice(0, 7).toLowerCase() === 'bearer ') return value.slice(7).trim();
  }
  return '';
}

// Claims-only check for the IAM-gated case, where Cloud Run has already
// stripped the real signature before forwarding. Sound ONLY because a
// stripped signature is itself evidence Cloud Run's IAM layer already
// authenticated the request — see verifyChatRequest's header comment for
// why this must never be inferred, only explicitly declared via
// trustCloudRunIam.
function claimsOnly(bearer, audiences) {
  const claims = decodeJwtPayloadUnverified(bearer);
  // email, not iss: for a Google-signed ID token, iss is a fixed Google
  // issuer regardless of which service account issued it, so it can never
  // distinguish Chat's SA from any other Google-signed caller — email
  // carries the actual identity signal. (This exact iss-vs-email confusion
  // has bitten identity checks elsewhere in this estate before.)
  if (claims.email !== CHAT_ISSUER && claims.iss !== CHAT_ISSUER) {
    throw new Error('bearer token was not issued by Google Chat');
  }
  const aud = String(claims.aud);
  if (!audiences.includes(aud)) {
    throw new Error(`invalid Chat bearer token audience "${aud}"`);
  }
  return claims;
}

/**
 * Verify a POST to /chat really came from Google Chat. Throws on any
 * failure — never a partial-trust return, matching verifyBotFrameworkAuth's
 * contract in teams-security.js.
 *
 * Two GENUINELY DIFFERENT verification paths depending on which
 * "Authentication Audience" mode the Chat app is configured with:
 *   - "App URL" (string audience, e.g. this service's own /chat URL): the
 *     token is signed with Google's standard OIDC keys. Verified via
 *     OAuth2Client.verifyIdToken() (signature + standard-issuer checks),
 *     THEN a SEPARATE check that payload.email === CHAT_ISSUER — never
 *     payload.iss for this path, per claimsOnly's comment above.
 *   - "Project Number" (numeric audience): the token is signed with Chat's
 *     own service-account x509 certs (CHAT_CERTS_URL), not a standard
 *     JWKS. Here iss DOES carry the identity signal (it's the SA's own
 *     email), so the library's own issuer check is the right one to use —
 *     passed as `issuers` to verifySignedJwtWithCertsAsync below.
 *
 * @param {(name: string) => string|null} getHeader
 * @param {{audiences: string[], trustCloudRunIam: boolean}} opts
 * @returns {Promise<object>} the verified (or, if bypassed/claims-only,
 *   trusted) token payload
 */
export async function verifyChatRequest(getHeader, { audiences, trustCloudRunIam }) {
  // Dev-only bypass — see config.js's chatDevBypassAuth comment for why
  // this is safe to leave in production code: NODE_ENV!=='production' is
  // checked HERE, at the call site, not just baked into the config value,
  // so the flag is structurally inert in any image built with
  // NODE_ENV=production (the Dockerfile's default) regardless of what
  // CHAT_DEV_BYPASS_AUTH is set to. Same shape as teams-security.js's own
  // bypass, for the same reason.
  if (config.chatDevBypassAuth && process.env.NODE_ENV !== 'production') {
    console.warn('[chat-security] WARNING: auth bypass active (CHAT_DEV_BYPASS_AUTH=1) — never set this in production');
    return { email: CHAT_ISSUER, aud: (audiences && audiences[0]) || 'dev-bypass', dev_bypass: true };
  }

  if (!audiences || !audiences.length) {
    throw new Error('CHAT_AUDIENCE is not set — refusing to serve /chat. Set it to this service\'s ' +
      "/chat URL and/or the Chat app's project number (comma-separated), matching the Chat API configuration.");
  }

  const bearer = extractBearer(getHeader);
  if (!bearer) throw new Error('missing bearer token');

  // Cloud Run strips and replaces a JWT's real signature before forwarding
  // it on an IAM-gated (--no-allow-unauthenticated) deployment. Real
  // cryptographic verification is therefore only possible on a public
  // (--allow-unauthenticated) deployment — which Chat needs anyway, for its
  // anonymous image-fetch second hop. On a gated deployment, only the
  // CLAIMS can be checked, relying on Cloud Run's own IAM having already
  // authenticated the caller — sound ONLY when explicitly declared via
  // trustCloudRunIam, never inferred: a public deployment must never accept
  // an unsigned token just because the flag happens to be unset. This
  // "guard only if configured, fail closed and loud if not" shape is
  // deliberate — an earlier version of exactly this shape left a
  // Cloudflare Worker open once elsewhere in this estate.
  if (!hasRealSignature(bearer)) {
    if (!trustCloudRunIam) {
      throw new Error('token signature was stripped by Cloud Run and cannot be verified here — ' +
        "if this service is deployed --no-allow-unauthenticated, set TRUST_CLOUD_RUN_IAM=1 to accept " +
        "Cloud Run's own authentication. Refusing.");
    }
    return claimsOnly(bearer, audiences);
  }

  const errors = [];
  for (const audience of audiences) {
    try {
      if (/^\d+$/.test(audience)) {
        let certs = await getX509Certs(false);
        try {
          const login = await oauth2Client.verifySignedJwtWithCertsAsync(bearer, certs, audience, [CHAT_ISSUER]);
          return login.getPayload();
        } catch (e) {
          // Unrecognized kid could mean Chat rotated its certs since our
          // last fetch — retry once with a forced refresh before giving up
          // on this audience, same "re-fetch on unknown kid" posture
          // teams-security.js gets for free from jose's createRemoteJWKSet.
          if (!/No pem found/.test((e && e.message) || '')) throw e;
          certs = await getX509Certs(true);
          const login = await oauth2Client.verifySignedJwtWithCertsAsync(bearer, certs, audience, [CHAT_ISSUER]);
          return login.getPayload();
        }
      } else {
        const ticket = await oauth2Client.verifyIdToken({ idToken: bearer, audience });
        const payload = ticket.getPayload();
        if (payload.email !== CHAT_ISSUER) {
          throw new Error(`token for audience "${audience}" was not issued by ${CHAT_ISSUER}`);
        }
        return payload;
      }
    } catch (e) {
      errors.push(`${audience}: ${(e && e.message) || e}`);
    }
  }
  throw new Error('invalid Chat bearer token (' + errors.join('; ') + ')');
}
