// src/adapters/registry.js — the platform-adapter registry. Each adapter is
// a thin descriptor object implementing the PlatformAdapter contract below;
// server.js iterates this array instead of hardcoding per-platform route
// mounts, and routes/mcp.js resolves /mcp's caller-supplied owner_key by
// walking the same array instead of a hand-written if/else ladder — that
// duplication (routes/mcp.js's old ownerKeyFrom) was the concrete symptom
// motivating this registry; see /home/curtis/.claude/plans/zany-petting-cray.md
// for the full "why now" reasoning (v1's own design doc flagged
// generalizing this as YAGNI "until a second surface needs it" — Teams was
// that surface and it never happened; Chat is the third).
//
// Adding a platform is: write one new adapters/<platform>.js implementing
// this contract, add it to the array below. Nothing else in server.js or
// routes/mcp.js needs to change — see ARCHITECTURE.md (once written) and
// the plan's own Telegram sketch for the concrete proof this generalizes.

/**
 * @typedef {Object} PlatformAdapter
 * @property {string} id                          'slack' | 'teams' | 'chat' | ...
 * @property {() => boolean} isConfigured          required env present? no side effects, safe to call every request
 * @property {() => string[]} missingConfig        names of unset required vars — for /status + boot log, NEVER values
 * @property {(app: import('hono').Hono) => void} registerRoutes
 *   Mounts this platform's OWN routes + OWN auth middleware onto the shared
 *   app. Deliberately NOT a generic "verify(req)" hook imposed by the
 *   registry loop — each platform's auth shape is genuinely different
 *   (Slack: HMAC over the raw body, verified before JSON parsing; Teams/Chat:
 *   per-request JWT verified inside the handler; a static secret header for
 *   Telegram, if added). Forcing one shape onto all of them would be the
 *   mistake this refactor exists to avoid.
 * @property {(...ids: string[]) => string} ownerKey
 *   Builds this platform's owner_key (see storage/index.js).
 * @property {(args: object) => string|null} ownerKeyFromMcpArgs
 *   Inspects /mcp's caller-supplied args shape and returns an owner_key if
 *   THIS platform recognizes the shape, else null.
 *
 * This bundles three genuinely separate concerns (route/auth mounting,
 * owner-key resolution, config-presence reporting) under one object because
 * with 2-4 platforms one interface is more legible than three parallel
 * registries — a pragmatic descriptor, not a single-responsibility
 * contract. Expect it to grow a method (e.g. an outbound health-check for
 * Chat's proactive-posting path) rather than staying frozen forever.
 */

import { slackAdapter } from './slack.js';
import { teamsAdapter } from './teams.js';
import { chatAdapter } from './chat.js';

export const adapters = [slackAdapter, teamsAdapter, chatAdapter];
