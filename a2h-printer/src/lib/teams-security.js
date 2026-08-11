// src/lib/teams-security.js — inbound Bot Framework request verification.
//
// Structurally different from slack-security.js's HMAC-over-raw-body: Bot
// Framework authenticates itself with a signed JWT (RS256) in the
// Authorization header, not a shared-secret signature. Unlike Slack's
// scheme, correctly implementing RSA/JWKS verification by hand is genuinely
// error-prone (key rotation, algorithm confusion, clock skew) — this uses
// `jose`, a vetted library, rather than hand-rolling it the way
// slack-security.js's HMAC check reasonably could be.
//
// What's verified, matching the documented Bot Framework minimum (the same
// checks botbuilder's JwtTokenValidation performs at its core):
//   1. Signature, against Bot Framework's own published JWKS.
//   2. issuer === https://api.botframework.com
//   3. audience === this bot's own App ID (TEAMS_APP_ID) — the thing that
//      stops a token issued for someone else's bot from being replayed here.
//   4. Standard exp/nbf validity (jose's jwtVerify checks these by default).
//
// NOT implemented (documented gap, not a silent one): government-cloud
// issuer variants, the Bot Framework Emulator's dev bypass, and channel-
// specific claim checks beyond issuer/audience. None of these apply to a
// production single-tenant Teams bot talking to commercial-cloud Teams,
// which is what this package targets — revisit if a deployer needs one of
// those specifically.

import { createRemoteJWKSet, jwtVerify } from 'jose';
import { config } from '../config.js';

const OPENID_CONFIG_URL = 'https://login.botframework.com/v1/.well-known/openidconfiguration';
const EXPECTED_ISSUER = 'https://api.botframework.com';

let jwks = null;

// Lazily created once per process — createRemoteJWKSet handles its own
// caching/refetch of the key set (and re-fetches on an unrecognized `kid`,
// which is how Bot Framework's own key rotation is handled without us
// needing to poll or expire anything ourselves).
async function getJwks() {
  if (jwks) return jwks;
  const resp = await fetch(OPENID_CONFIG_URL);
  const { jwks_uri } = await resp.json();
  jwks = createRemoteJWKSet(new URL(jwks_uri));
  return jwks;
}

// Returns the verified JWT payload on success, or throws with a message
// safe to log (never echoes the token itself). Callers must treat a throw
// as "reject the request" — there is no partial-trust return value.
export async function verifyBotFrameworkAuth(authorizationHeader, expectedAppId) {
  // Dev-only bypass — see config.js's teamsDevBypassAuth comment for why this
  // is safe to leave in production code: NODE_ENV!=='production' is checked
  // HERE, at the call site, not just baked into the config value, so the
  // flag is structurally inert in any image built with NODE_ENV=production
  // (the Dockerfile's default) regardless of what TEAMS_DEV_BYPASS_AUTH is
  // set to. Named after the exact gap this file's own header comment already
  // flagged as missing: "the Bot Framework Emulator's dev bypass."
  if (config.teamsDevBypassAuth && process.env.NODE_ENV !== 'production') {
    console.warn('[teams-security] WARNING: auth bypass active (TEAMS_DEV_BYPASS_AUTH=1) — never set this in production');
    return { iss: EXPECTED_ISSUER, aud: expectedAppId, dev_bypass: true };
  }

  if (!authorizationHeader || !authorizationHeader.startsWith('Bearer ')) {
    throw new Error('missing or malformed Authorization header');
  }
  const token = authorizationHeader.slice('Bearer '.length);
  const keys = await getJwks();
  const { payload } = await jwtVerify(token, keys, {
    issuer: EXPECTED_ISSUER,
    audience: expectedAppId,
  });
  return payload;
}
