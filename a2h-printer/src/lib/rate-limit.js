// src/lib/rate-limit.js — a minimal, dependency-free per-IP request limiter.
//
// Roast-panel finding, 2026-08-12: zero rate limiting existed on any route.
// The bearer token and Slack/Teams signature verification are still the
// REAL security controls — this is defense-in-depth against volume abuse
// (a leaked token hammered, or a webhook URL discovered and flooded), not
// a substitute for them. Deliberately generous defaults: this must never
// throttle a legitimate single workspace's real traffic.
//
// Client IP is read from X-Forwarded-For's first hop, which is trustworthy
// specifically on Cloud Run (Google's own frontend sets it; a request
// cannot reach this process without passing through it first — see
// deploy/cloud-run/deploy.sh, the documented deploy target). On a
// self-hosted deployment behind YOUR OWN reverse proxy, this header is
// only as trustworthy as that proxy's own configuration to strip/overwrite
// any client-supplied value — the same caveat every X-Forwarded-For-based
// control has. Falls back to the raw socket address (Docker Compose /
// bare-metal, no proxy in front) when the header is absent.
//
// Fixed-window, in-memory, single-instance only — matches this app's own
// deploy posture (`--max-instances 1` in deploy.sh); does not need to
// survive a restart or coordinate across instances that don't exist.

import { getConnInfo } from '@hono/node-server/conninfo';

const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 120; // generous: 2 req/sec sustained, well above one workspace's real traffic

const buckets = new Map(); // ip -> { count, windowStart }

function clientIp(c) {
  const xff = c.req.header('x-forwarded-for');
  if (xff) return xff.split(',')[0].trim();
  // Real @hono/node-server helper, not a guessed internal shape — see
  // node_modules/hono/dist/helper/conninfo/types.d.ts for the ConnInfo type.
  return getConnInfo(c).remote.address || 'unknown';
}

export async function rateLimit(c, next) {
  const ip = clientIp(c);
  const now = Date.now();
  let bucket = buckets.get(ip);
  if (!bucket || now - bucket.windowStart >= WINDOW_MS) {
    bucket = { count: 0, windowStart: now };
    buckets.set(ip, bucket);
  }
  bucket.count++;
  if (bucket.count > MAX_PER_WINDOW) {
    return c.json({ error: 'rate limit exceeded, try again shortly' }, 429);
  }
  // Opportunistic cleanup so `buckets` doesn't grow unbounded under many
  // distinct IPs over a long-running process — cheap, only runs on the
  // rare request that lands exactly on a full bucket.
  if (buckets.size > 10_000) {
    for (const [k, v] of buckets) {
      if (now - v.windowStart >= WINDOW_MS) buckets.delete(k);
    }
  }
  await next();
}
