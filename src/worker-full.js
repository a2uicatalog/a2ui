// src/worker-full.js — the gated full.a2uicatalog.ai site. Serves
// public-full/ as static assets (unchanged), plus one new route,
// POST /authoring/api/lift, running the lift step server-side via Vertex AI.
//
// REAL BOUNDARY, same pattern as the rest of the Authoring feature: this
// file is public (tracked in a2ui-catalogue) but holds no content itself —
// the archetype/prompt data it reads (env.ASSETS fetch of archetypes.json)
// only exists behind the same Cloudflare Access gate as everything else
// under full.a2uicatalog.ai.
//
// Auth model:
//   1. Cloudflare Access already gates who reaches this Worker at all
//      (full.a2uicatalog.ai, Google IdP, allowed_identity: curtis@krygier.fr).
//   2. This handler ALSO verifies the Cf-Access-Jwt-Assertion header itself
//      — defense in depth, never trust the network perimeter alone.
//   3. Vertex AI is called as a dedicated, narrowly-scoped Service Account
//      (blog-authoring-lift@static-hangout-500821-d3, roles/aiplatform.user
//      ONLY on that one project) via the standard JWT-bearer OAuth2 flow —
//      not Curtis's own broad-scope user identity. See a2uithoughts.md,
//      2026-07-19, for the blast-radius reasoning behind that choice.

const CF_TEAM = "quiet-star-95ae";
const ALLOWED_ACCESS_EMAIL = "curtis@krygier.fr";
const VERTEX_PROJECT = "static-hangout-500821-d3";
const VERTEX_LOCATION = "us-central1";
const VERTEX_MODEL = "gemini-2.5-flash";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/authoring/api/lift" && request.method === "POST") {
      return handleLift(request, env);
    }
    if (url.pathname === "/authoring/api/dispatch" && request.method === "POST") {
      return handleDispatch(request, env);
    }
    return env.ASSETS.fetch(request);
  },
};

async function handleLift(request, env) {
  try {
    await verifyAccessJwt(request, env);
  } catch (e) {
    return json({ error: `Access verification failed: ${e.message}` }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }
  const { draft, archetype: archetypeKey } = body;
  if (!draft || !archetypeKey) {
    return json({ error: "Missing 'draft' or 'archetype' in request body" }, 400);
  }

  const archetypesResp = await env.ASSETS.fetch(new URL("/authoring/archetypes.json", request.url));
  if (!archetypesResp.ok) {
    return json({ error: "Could not load archetypes.json from assets" }, 500);
  }
  const archetypes = await archetypesResp.json();
  const archetype = archetypes[archetypeKey];
  if (!archetype) {
    return json({ error: `Unknown archetype: ${archetypeKey}` }, 400);
  }

  const prompt = buildServerPrompt(archetype, draft);

  let accessToken;
  try {
    accessToken = await getVertexAccessToken(env.VERTEX_SA_KEY);
  } catch (e) {
    return json({ error: `Vertex AI auth failed: ${e.message}` }, 500);
  }

  let modelOutput;
  try {
    modelOutput = await callVertexGemini(accessToken, prompt);
  } catch (e) {
    return json({ error: `Vertex AI call failed: ${e.message}` }, 502);
  }

  return json({ archetype: archetypeKey, output: modelOutput });
}

// Deliberately a SEPARATE action from handleLift, not automatic on every
// format call — the human reviews the formatted output on the page first
// (§4 of the playbook: nothing invented, labels read well, etc.) and only
// explicitly asks for a PR to be opened. This is "review before publish"
// applied at PR-creation time too, not only at merge time. The PR itself
// still requires a human merge — this step never publishes anything, it
// only queues a reviewable change.
async function handleDispatch(request, env) {
  try {
    await verifyAccessJwt(request, env);
  } catch (e) {
    return json({ error: `Access verification failed: ${e.message}` }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }
  const { markdown } = body;
  if (!markdown) {
    return json({ error: "Missing 'markdown' in request body" }, 400);
  }

  const resp = await fetch(
    "https://api.github.com/repos/a2uicatalog/a2ui-private/dispatches",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "a2uicatalog-full-worker",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        event_type: "lift-draft",
        client_payload: { markdown },
      }),
    }
  );
  if (!resp.ok) {
    return json({ error: `GitHub dispatch failed: ${resp.status} ${await resp.text()}` }, 502);
  }

  return json({ dispatched: true });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json" },
  });
}

// ---- Cloudflare Access JWT verification (defense in depth) ----

async function verifyAccessJwt(request, env) {
  const token = request.headers.get("Cf-Access-Jwt-Assertion");

  // Dev-only bypass: wrangler dev never has real Access headers in front of
  // it. Only honored via .dev.vars (never committed), never in the deployed
  // config — see wrangler-full.toml, which has no such var.
  if (env.DEV_SKIP_ACCESS_CHECK === "1") return;

  if (!token) throw new Error("no Cf-Access-Jwt-Assertion header");

  const certsUrl = `https://${CF_TEAM}.cloudflareaccess.com/cdn-cgi/access/certs`;
  const certsResp = await fetch(certsUrl);
  const certs = await certsResp.json();

  const [headerB64, payloadB64, sigB64] = token.split(".");
  const header = JSON.parse(base64UrlDecodeToString(headerB64));
  const payload = JSON.parse(base64UrlDecodeToString(payloadB64));

  const jwk = certs.keys.find((k) => k.kid === header.kid);
  if (!jwk) throw new Error("no matching JWKS key for kid");

  const key = await crypto.subtle.importKey(
    "jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]
  );
  const signature = base64UrlDecodeToBuffer(sigB64);
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, signature, data);
  if (!valid) throw new Error("signature verification failed");

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp && payload.exp < now) throw new Error("token expired");
  if (payload.email !== ALLOWED_ACCESS_EMAIL) throw new Error(`unexpected identity: ${payload.email}`);
}

function base64UrlDecodeToString(s) {
  return atob(s.replace(/-/g, "+").replace(/_/g, "/"));
}
function base64UrlDecodeToBuffer(s) {
  const str = base64UrlDecodeToString(s);
  const bytes = new Uint8Array(str.length);
  for (let i = 0; i < str.length; i++) bytes[i] = str.charCodeAt(i);
  return bytes.buffer;
}

// ---- Service Account JWT-bearer OAuth2 (Vertex AI auth) ----

async function getVertexAccessToken(saKeyJson) {
  const key = JSON.parse(saKeyJson);
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  const claims = {
    iss: key.client_email,
    scope: "https://www.googleapis.com/auth/cloud-platform",
    aud: "https://oauth2.googleapis.com/token",
    exp: now + 3600,
    iat: now,
  };
  const encHeader = base64UrlEncode(JSON.stringify(header));
  const encClaims = base64UrlEncode(JSON.stringify(claims));
  const signingInput = `${encHeader}.${encClaims}`;

  const cryptoKey = await importPkcs8PrivateKey(key.private_key);
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5", cryptoKey, new TextEncoder().encode(signingInput)
  );
  const jwt = `${signingInput}.${base64UrlEncodeBuffer(signature)}`;

  const resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }),
  });
  if (!resp.ok) throw new Error(`token exchange failed: ${resp.status} ${await resp.text()}`);
  const data = await resp.json();
  return data.access_token;
}

async function importPkcs8PrivateKey(pem) {
  const b64 = pem
    .replace(/-----BEGIN PRIVATE KEY-----/, "")
    .replace(/-----END PRIVATE KEY-----/, "")
    .replace(/\s/g, "");
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return crypto.subtle.importKey(
    "pkcs8", bytes.buffer, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]
  );
}

function base64UrlEncode(str) {
  return base64UrlEncodeBuffer(new TextEncoder().encode(str));
}
function base64UrlEncodeBuffer(buf) {
  const bytes = new Uint8Array(buf);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// ---- Vertex AI generateContent ----

async function callVertexGemini(accessToken, prompt) {
  const url = `https://${VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/${VERTEX_PROJECT}/locations/${VERTEX_LOCATION}/publishers/google/models/${VERTEX_MODEL}:generateContent`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
    }),
  });
  if (!resp.ok) throw new Error(`${resp.status} ${await resp.text()}`);
  const data = await resp.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error(`no text in response: ${JSON.stringify(data)}`);
  return text;
}

// ---- Prompt construction ----
//
// Server-side variant of gen_authoring.py's client-side buildPrompt().
// Deliberately NOT the same text: NNN/volume are never asked for here. A
// single-shot API call can't "ask" for anything the way an interactive
// chat prompt can, and both are resolved deterministically downstream by
// whatever step actually has real repo access (the GitHub Actions
// dispatch), never guessed by the model. See a2uithoughts.md, 2026-07-19,
// for why that split matters — it's what closes the volume/NNN defect
// class structurally instead of by reminder.

function buildServerPrompt(a, draft) {
  const slotList = a.slots.map((s) => `  <!-- slot: ${s} -->`).join("\n");
  return `You are formatting a rough draft into this blog's exact parser conventions
AND annotating it for future graduation to a live A2UI ComponentId/ChildList
template. Output ONLY the final markdown file (frontmatter + body). No
commentary, no fences around the whole thing, no explanation outside the
Phase 4 report. Invent nothing not present in the draft - sparseness in the
draft stays sparse in the output; never fabricate a section, quote, caveat,
or number to fill a template slot.

PHASE 0 - Frontmatter
Emit: title, series, date, summary, read_minutes
Do NOT emit a volume field - it is assigned deterministically by the
publish pipeline after this step, not by you. All five fields above are
required by the parser or the build fails. Infer read_minutes from word
count (~200 wpm) if not given. If this post is one part of a named
multi-part arc, say so as plain text in the title itself (e.g.
"... (Part 2)") - there is no separate part-number field.

PHASE 0.5 - Slug
State this on its own line, before the formatted output:
  Proposed slug: <slug>
<slug> is lowercase, hyphenated, short, derived from the title. Do not
propose a filename number (NNN) or a volume value - both are resolved
deterministically outside this step.

PHASE 1 - Archetype (fixed for this run)
Archetype: ${a.label}
Spine: ${a.spine}
Signals this archetype fits: ${a.signals}
If the draft clearly does NOT fit this spine, say so in Phase 4 instead of
forcing it - don't silently reshape content into a spine it doesn't have.

PHASE 2 - Structure into H2 sections matching the spine
${a.phase2}
Every heading gets {label="Short"} if the natural heading is longer than
~3 words or doesn't front-load its distinctive word.

PHASE 2.5 - Template alignment (for future ComponentId/ChildList graduation)
This archetype's target composition:
  ${a.childlist}
Immediately before each section that corresponds to one of these slots,
insert an HTML comment naming it, e.g.:
${slotList}
Comments are invisible in the rendered post today - they're forward
compatibility for the day this graduates from markdown to a live
ComponentId/ChildList payload. Skip slots the draft doesn't support rather
than inventing content to fill them - an absent slot is a true fact about
this draft, not an error.

PHASE 3 - Marks
- The single most quotable line (if one exists) becomes \`> [!QUOTE] <line>\`.
  Zero or one per major section; two is the ceiling for the whole post.
- If a specific line is a standout takeaway worth pulling out (not every
  line), mark it \`> [!TAKEAWAY: <2-4 word label>] <line>\` - the label
  names what THAT line is actually about, never a fixed phrase reused
  across posts. Reserve the literal word "frugality" for posts that are
  genuinely about frugality - don't force it into other series.
- Fenced code blocks stay ordinary triple-backtick.
- Real markdown tables where the draft has tabular data.

PHASE 4 - Report
After the output, list on separate lines:
- Whether the draft actually fit the ${a.label} spine, or where it strained
- Any heading you added an explicit {label=...} to, and why
- Which ComponentId slots got skipped (no content for them) vs used
- Anything you could NOT confidently structure - flag it, don't paper over it

---
DRAFT TO FORMAT:
${draft}`;
}
