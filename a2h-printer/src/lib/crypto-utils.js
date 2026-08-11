// Timing-safe string compare. Extracted from mcp-worker/src/oauth.js's
// safeEqual — that file also has Cloudflare Access / KV-bound OAuth logic
// this package doesn't need (no reader-identity system in v1, see plan
// decision #1), so only this one pure function is ported, not the file.
export function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// Relocated verbatim from slack-blocks.js (2026-08-11, see
// /home/curtis/.claude/plans/zany-petting-cray.md's "Render-signing HMAC —
// relocate, don't duplicate") — genuinely platform-agnostic HMAC-SHA256-
// over-gzip, not Slack-specific at all. Moved here so Chat's render path
// (lib/render-to-chat.js) can call it directly, without going through
// slack-blocks.js's Slack-Block-Kit-shaped eImageRender wrapper.
//
// Mints the SAME signed-URL scheme `cloud-run-renderer/server.py`'s
// _encode_block_qs/_sign already verifies (gzip -> urlsafe-base64,
// HMAC-SHA256 truncated to 16 hex chars) rather than inventing a new one —
// this must byte-for-byte match that service or it 403s every URL (verified
// against the live service before this first landed in slack-blocks.js,
// both from Python and from this exact function; the relocation itself was
// verified byte-identical against the pre-move output before landing).
//
// ASYNC — the one function in this file that needs real crypto (HMAC-SHA256
// via Web Crypto, available in both a Cloudflare Worker and plain Node,
// confirmed, so no environment branch). renderConfig is an explicit
// PARAMETER, never read from a global `env`, so this stays importable
// identically in both runtimes.
//
// Only the Chromium WORK happens later, out of band, when the platform's own
// crawler fetches the URL — this function does no network I/O itself, so a
// webhook's ack-latency budget is never at risk from a slow or cold-starting
// render.
export async function signRenderUrl(atomType, props, renderConfig) {
  const { signingKey, baseUrl, width = 620, theme } = renderConfig;
  // theme is OPTIONAL and omitted from the payload when unset — existing
  // callers (Slack, Chat) that never pass it get byte-identical output to
  // before this was added. teams-blocks.js's own local signRenderUrl copy
  // already proved `{theme:'light'}` fixes dark-background rendering on
  // light-mode hosts (2026-08-08); added here so copilotkit/a2ui-bridge.ts
  // can delegate to ONE shared implementation instead of a third local copy.
  const spec = theme ? { block: { type: atomType, ...props }, width, theme } : { block: { type: atomType, ...props }, width };
  const payload = JSON.stringify(spec);
  const cs = new CompressionStream('gzip');
  const writer = cs.writable.getWriter();
  writer.write(new TextEncoder().encode(payload));
  writer.close();
  const compressed = new Uint8Array(await new Response(cs.readable).arrayBuffer());
  let bin = '';
  for (const b of compressed) bin += String.fromCharCode(b);
  const token = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(signingKey), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(token));
  const sig = Array.from(new Uint8Array(mac)).map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
  return `${baseUrl}/render.png?b=${token}.${sig}`;
}
