// src/storage/sqlite.js — default storage backend, replacing profile.js's
// Durable Object. Same op contract (get/patch/save/list/delete/summary), but
// a single SQLite file serving every identity via an `owner_key` column
// instead of one-DO-instance-per-key. v1 has exactly one identity shape
// (`slack:{team_id}:{user_id}`) — no reader `sub`, no nonce singleton, no
// link tables — since the account-linking flow was dropped (plan decision
// #1). See profile.js in a2ui-private/mcp-worker for the ported-from op
// contract and MAX_READINGS rationale.
import Database from 'better-sqlite3';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const MAX_READINGS = 200;

const SCHEMA = `
CREATE TABLE IF NOT EXISTS profile (
  owner_key TEXT NOT NULL,
  k         TEXT NOT NULL,
  v         TEXT NOT NULL,
  ts        INTEGER NOT NULL,
  PRIMARY KEY (owner_key, k)
);
CREATE TABLE IF NOT EXISTS readings (
  owner_key     TEXT NOT NULL,
  id            TEXT NOT NULL,
  runbook       TEXT NOT NULL,
  source_url    TEXT,
  source_title  TEXT,
  title         TEXT,
  lens          TEXT,
  url           TEXT,
  stamped_at    INTEGER NOT NULL,
  payload_p     TEXT,
  payload_bytes INTEGER,
  PRIMARY KEY (owner_key, id)
);
CREATE INDEX IF NOT EXISTS readings_by_time ON readings (owner_key, stamped_at DESC);
CREATE INDEX IF NOT EXISTS readings_by_runbook ON readings (owner_key, runbook, stamped_at DESC);
`;

let db = null;

// Opened once per process, lazily — most routes never touch storage (the
// signature-verification-only /slack/interactivity paths, health checks).
function open(sqlitePath) {
  if (db) return db;
  mkdirSync(dirname(sqlitePath), { recursive: true });
  db = new Database(sqlitePath);
  db.pragma('journal_mode = WAL');
  db.exec(SCHEMA);
  return db;
}

// Fail-closed by construction: every method below either returns a value or
// throws — there is no path that silently returns "empty" on a real DB
// fault. Callers (routes) must treat a thrown error as "storage unavailable,
// deny the request", never as "no data, proceed" — this was a deliberate,
// non-negotiable property of the Durable Object design being replaced (see
// plan decision #3) and it must survive the swap to SQLite.
export function createSqliteStore(sqlitePath, ownerKey) {
  const conn = open(sqlitePath);

  function readProfile() {
    const rows = conn.prepare('SELECT k, v FROM profile WHERE owner_key = ?').all(ownerKey);
    const out = {};
    for (const row of rows) {
      try { out[row.k] = JSON.parse(row.v); } catch (e) { out[row.k] = row.v; }
    }
    return out;
  }

  return {
    get: async () => ({ profile: readProfile() }),

    patch: async (patch = {}) => {
      const now = Date.now();
      const del = conn.prepare('DELETE FROM profile WHERE owner_key = ? AND k = ?');
      const upsert = conn.prepare(
        'INSERT INTO profile (owner_key, k, v, ts) VALUES (?, ?, ?, ?) ' +
        'ON CONFLICT(owner_key, k) DO UPDATE SET v = excluded.v, ts = excluded.ts');
      const tx = conn.transaction((entries) => {
        for (const [k, v] of entries) {
          if (v === null || v === undefined) del.run(ownerKey, k);
          else upsert.run(ownerKey, k, JSON.stringify(v), now);
        }
      });
      tx(Object.entries(patch));
      return { profile: readProfile() };
    },

    save: async (r = {}) => {
      const id = r.id || (Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8));
      conn.prepare(
        'INSERT OR REPLACE INTO readings ' +
        '(owner_key, id, runbook, source_url, source_title, title, lens, url, stamped_at, payload_p, payload_bytes) ' +
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
      ).run(
        ownerKey, id, r.runbook || 'unknown', r.source_url || null, r.source_title || null,
        r.title || null, r.lens || null, r.url || null, r.stamped_at || Date.now(),
        r.payload_p || null, r.payload_p ? r.payload_p.length : null,
      );
      // Prune oldest beyond the cap, scoped to this owner — bounded per-Slack-user
      // store, no background job needed.
      conn.prepare(
        'DELETE FROM readings WHERE owner_key = ? AND id NOT IN ' +
        '(SELECT id FROM readings WHERE owner_key = ? ORDER BY stamped_at DESC LIMIT ?)'
      ).run(ownerKey, ownerKey, MAX_READINGS);
      return { id };
    },

    list: async (runbook, limit) => {
      const n = Math.min(Math.max(parseInt(limit || 20, 10) || 20, 1), 100);
      const rows = runbook
        ? conn.prepare('SELECT * FROM readings WHERE owner_key = ? AND runbook = ? ORDER BY stamped_at DESC LIMIT ?')
            .all(ownerKey, runbook, n)
        : conn.prepare('SELECT * FROM readings WHERE owner_key = ? ORDER BY stamped_at DESC LIMIT ?')
            .all(ownerKey, n);
      return { readings: rows };
    },

    delete: async (ids) => {
      const list = (Array.isArray(ids) ? ids : [ids]).filter((x) => typeof x === 'string' && x);
      if (!list.length) return { deleted: 0 };
      const placeholders = list.map(() => '?').join(',');
      const info = conn.prepare(
        `DELETE FROM readings WHERE owner_key = ? AND id IN (${placeholders})`
      ).run(ownerKey, ...list);
      return { deleted: info.changes || 0 };
    },

    summary: async () => {
      const total = conn.prepare('SELECT COUNT(*) AS n FROM readings WHERE owner_key = ?').get(ownerKey).n;
      const readings = conn.prepare(
        'SELECT * FROM readings WHERE owner_key = ? ORDER BY stamped_at DESC LIMIT 10'
      ).all(ownerKey);
      return { profile: readProfile(), readings, total };
    },
  };
}
