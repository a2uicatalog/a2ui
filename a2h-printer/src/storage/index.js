// src/storage/index.js — storage factory. SQLite by default; DATABASE_URL
// switches to Postgres behind the identical op contract (plan decision #3).
// Postgres backend isn't built yet — failing loudly here rather than
// silently falling back to SQLite matters: a deployer who set DATABASE_URL
// expects THAT store, and silently using a different one is exactly the
// kind of fail-open behavior plan decision #3 rules out.
import { config } from '../config.js';
import { createSqliteStore } from './sqlite.js';

export function slackOwnerKey(teamId, userId) {
  return `slack:${teamId}:${userId}`;
}

// Teams' closest equivalent to Slack's team_id is the AAD tenant id
// (activity.conversation.tenantId), and to user_id is the AAD object id in
// activity.from.aadObjectId — both stable identifiers, unlike Slack's
// display-oriented fields. Distinct namespace prefix so a Slack and a Teams
// identity can never collide in storage or in MCP_ALLOWED_OWNERS.
export function teamsOwnerKey(tenantId, userId) {
  return `teams:${tenantId}:${userId}`;
}

// Added ahead of the Chat adapter itself (see plan phase 5) so phase 7 needs
// zero storage-layer changes. Chat's equivalent of Slack's team_id/Teams'
// tenantId is the Space resource name (spaces/AAAA...), and of user_id the
// User resource name (users/1234567890...) — both stable, matching why
// teamsOwnerKey prefers aadObjectId over the display-only from.id.
export function chatOwnerKey(spaceName, userName) {
  return `chat:${spaceName}:${userName}`;
}

export function getStore(ownerKey) {
  if (config.databaseUrl) {
    throw new Error(
      'DATABASE_URL is set but the Postgres backend is not implemented yet — ' +
      'refusing to silently fall back to SQLite. Unset DATABASE_URL to use the default store.'
    );
  }
  return createSqliteStore(config.sqlitePath, ownerKey);
}
