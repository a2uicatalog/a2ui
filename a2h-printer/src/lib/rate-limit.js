// src/lib/rate-limit.js — a minimal, dependency-free per-IP request limiter.
//
// Roast-panel finding, 2026-08-12: zero rate limiting existed on any route.
// The bearer token and Slack/Teams signature verification are still the
// REAL security controls — this is defense-in-depth against volume abuse
// (a leaked token hammered, or a webhook URL discovered and flooded), not
// a substitute for them. Deliberately generous defaults: this must never
// throttle a legitimate single workspace's real traffic.
//
// ROUND 2 FIX (2026-08-12): the original version was ONE global bucket
// shared by every route, keyed by IP. That's wrong for this app
// specifically: Slack/Teams/Chat webhooks are POSTed by THAT PLATFORM'S
// OWN infrastructure, not by individual end users — an entire workspace's
// real traffic shares whatever IP Slack's/Microsoft's/Google's own
// outbound infra presents. A single shared bucket meant a legitimately
// busy workspace's webhook volume could exhaust the same budget a
// /mcp agent batch operation needed, and vice versa. createRateLimiter()
// below makes a NEW, independently-bucketed limiter each call — server.js
// applies one instance per route GROUP (webhook routes vs /mcp), so a
// burst on one can never starve the other. IP-keying itself is kept
// (rejected token-keying for /mcp specifically: there is exactly ONE
// valid MCP_AUTH_TOKEN per deployment, not one per caller, so keying by
// token would merge a leaked-token attacker's traffic into the SAME
// bucket as the legitimate caller instead of separating them — IP-keying
// is the one that can actually tell those two apart).
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

function clientIp(c) {
  const xff = c.req.header('x-forwarded-for');
  if (xff) return xff.split(',')[0].trim();
  // Real @hono/node-server helper, not a guessed internal shape — see
  // node_modules/hono/dist/helper/conninfo/types.d.ts for the ConnInfo type.
  return getConnInfo(c).remote.address || 'unknown';
}

// Each call returns a middleware with its OWN independent bucket Map —
// this is what makes two calls (e.g. one for webhook routes, one for
// /mcp) genuinely isolated from each other rather than sharing state.
export function createRateLimiter({ maxPerWindow, windowMs = 60_000 }) {
  const buckets = new Map(); // ip -> { count, windowStart }

  return async function rateLimit(c, next) {
    const ip = clientIp(c);
    const now = Date.now();
    let bucket = buckets.get(ip);
    if (!bucket || now - bucket.windowStart >= windowMs) {
      bucket = { count: 0, windowStart: now };
      buckets.set(ip, bucket);
    }
    bucket.count++;
    if (bucket.count > maxPerWindow) {
      return c.json({ error: 'rate limit exceeded, try again shortly' }, 429);
    }
    // Opportunistic cleanup so `buckets` doesn't grow unbounded under many
    // distinct IPs over a long-running process — cheap, only runs on the
    // rare request that lands exactly on a full bucket.
    if (buckets.size > 10_000) {
      for (const [k, v] of buckets) {
        if (now - v.windowStart >= windowMs) buckets.delete(k);
      }
    }
    await next();
  };
}
