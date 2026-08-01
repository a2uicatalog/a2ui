# cloud-run-renderer

A headless "print any atom" render engine, plus a working Google Chat app
built on top of it. Chat's native `cardsV2` widget set is fixed —
`decoratedText`, `textParagraph`, `image`, `buttonList` — no custom layout,
no real typography, no charts beyond what Google ships. This service
renders any atom from the catalogue to a real PNG/GIF using headless
Chromium (the exact same HTML/CSS every other surface in this repo uses,
not a second, drifting copy) and hands Chat a plain image URL to display.
Full visual fidelity, on a surface that was never going to get custom
widgets natively.

By the end of this tutorial you'll have a real Chat bot, running on your
own Google Cloud project, answering `workspace stats` and `weather` with
live, server-rendered visuals. Nothing here talks to any other private
service — the two live data sources it calls (Google's own public
Workspace status feed, and Open-Meteo) are free and need no API key.

## Before you start

- A Google Cloud project with billing enabled (you'll deploy one Cloud Run
  service — see the cost note in Step 2 before going further).
- The `gcloud` CLI, installed and authenticated (`gcloud auth login`).
- Python 3 locally, only for Step 1's verification — not required once
  you're deploying.
- No API keys, no paid tiers, no Workspace admin rights beyond what's
  needed to install a Chat app for yourself or your domain.

## Step 1 — Get the render engine working locally

Do this before touching Cloud Run — it isolates "does the renderer work"
from "is my deployment/Chat config right," so if something breaks later
you already know which half is solid.

```bash
pip install -r cloud-run-renderer/requirements.txt
playwright install chromium
RENDER_SIGNING_KEY=dev-key CHAT_AUDIENCE=http://localhost:8080/chat \
  python3 cloud-run-renderer/server.py
```

The two env vars are the same ones the deployed service uses. The auth
checks are always on — there is no local bypass flag, deliberately, so
that what you exercise here is what runs in production.

In another shell:

```bash
curl -X POST localhost:8080/render -H "Content-Type: application/json" \
  -H "X-Render-Token: dev-key" \
  -d '{"block": {"type": "gauge_sla", "value": 82, "max_value": 100, "label": "P1 Incident SLA"}}' \
  -o out.png
```

Open `out.png` — you should see a real rendered gauge. Drop the
`X-Render-Token` header and you get a 403 instead; that's the guard
working.

`/chat` is the one route you can't exercise with a header, because it
authenticates the bearer token Google Chat itself signs — nothing local
can produce one. Verify the same code path through `/deck`, which runs
the identical command routing:

```bash
curl -H "X-Render-Token: dev-key" 'localhost:8080/deck?text=sla+82+gif'
```

This returns the encoded, signed query strings `/chat` would have put in
its card — a `deck_b` for the whole deck and a `cards[].b` per card. Open
`localhost:8080/render.gif?b=<deck_b>` in a browser: no header needed,
because the signature in the token is the auth. That's the actual rendered
GIF. If both of these worked, the render engine is solid and everything
left is deployment + Chat configuration.

## Step 2 — Deploy to Cloud Run

Chat's `image` widget does an **anonymous** GET on whatever `imageUrl` you
give it — no bearer token, no signed-in identity, nothing. That's a hard
constraint from Google's side, not a choice made here, and it's why the
deploy command below uses `--allow-unauthenticated`.

One-time setup — create the Secret Manager secret. It does double duty:
it signs the image tokens *and* it is the shared key every non-Chat caller
sends as `X-Render-Token`. Both are explained under "Security
considerations"; this is a deliberate one-time manual step, not scripted.

```bash
gcloud secrets create render-signing-key \
  --project=YOUR_PROJECT --data-file=<(openssl rand -hex 32)
```

```bash
gcloud run deploy YOUR_SERVICE_NAME \
  --source . \
  --project YOUR_PROJECT \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --max-instances 3 \
  --concurrency 4 \
  --set-secrets RENDER_SIGNING_KEY=render-signing-key:latest
```

Note the URL `gcloud` prints at the end — you'll need it in Step 3.

**`--allow-unauthenticated` does not mean unauthenticated.** Every route
that costs real money authenticates itself in-app, because Cloud Run's
public/private switch is per *service*, not per *route*: the moment you
make `/render.png` reachable for Chat, you make everything else on the
deployment reachable too. So:

| Route | What gets you in |
|---|---|
| `POST /render`, `POST /render-deck`, `GET /deck` | `X-Render-Token: $RENDER_SIGNING_KEY` header |
| `GET /render.png`, `GET /render.gif` | a valid HMAC signature on the `?b=` token — i.e. a URL this service itself minted |
| `POST /chat` | a bearer token Google Chat signed, verified against `CHAT_AUDIENCE` |
| `GET /status` | nothing (liveness only, returns `{"ok":true}`) |

Come back after Step 3 and set `CHAT_AUDIENCE` — until you do, `/chat`
refuses every request. It takes a comma-separated list and accepts a token
matching any entry, so set both forms and you cannot get it wrong:

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --project YOUR_PROJECT --region YOUR_REGION \
  --update-env-vars "CHAT_AUDIENCE=YOUR_CHAT_APP_PROJECT_NUMBER,https://YOUR_SERVICE_URL/chat"
```

Both values name your own app, so listing both weakens nothing — see
Step 3 for why you may not be able to tell which one Chat will send.

**Don't drop `--max-instances`.** Every render launches a real headless
Chromium process. The route guards above mean an anonymous caller can't
trigger one, but `--max-instances` is the layer that doesn't depend on any
of that being correct: a hard ceiling on how many can run at once, whatever
else goes wrong.

The code itself carries three more layers on top of that, worth knowing
about rather than just trusting:

- **`width`/deck-size bounds** — `MAX_RENDER_WIDTH` (2000px) and
  `MAX_DECK_BLOCKS` (12) reject an oversized single request outright.
- **A payload-size cap** — `MAX_BLOCK_JSON_BYTES` (50KB) catches the gap
  those two don't: an in-bounds width and block count with one field
  (e.g. a chart's data array) padded enormous. `MAX_CONTENT_LENGTH` (2MB)
  on the Flask app rejects an oversized request body before any JSON
  parsing even runs.
- **Signed render tokens** — `/render.png` and `/render.gif` must stay
  reachable with no auth check (that's Chat's own constraint, not a choice
  made here), but every token this service generates is HMAC-signed, and
  a forged or guessed one gets an instant 403 before any rendering starts.
  Only URLs this service itself produced are ever honored. **Set
  `RENDER_SIGNING_KEY` explicitly before deploying** — Secret Manager /
  `--set-secrets`, same posture as other credentials in this repo. Without
  it, the service generates a random key per process, which will cause
  spurious verification failures across a multi-instance deployment the
  moment a request lands on a different instance than the one that signed
  it.
- **A render-rate limit** — `MAX_RENDERS_PER_MINUTE` (30) is a real,
  computable cost ceiling: unlike `--max-instances` (which only bounds
  *concurrent* cost), this bounds cost *over time*, regardless of how long
  an attack runs. It's per-process, not a true cross-instance global limit
  — with `--max-instances 3` the effective ceiling is up to 3x this value
  if traffic spreads across instances. A real global limit needs a shared
  store (Redis/Memorystore); this in-process version still cuts
  worst-case cost substantially and is what ships by default.

None of this makes the *hostname* anything other than public — Chat's
`image` widget fetch is anonymous by Google's own design, and there's no
way around that for this specific integration. What it does do: a caller
without either a valid token or a validly-signed URL gets a cheap, instant
403 instead of a real Chromium launch, and even sustained valid-shaped
traffic is bounded to a knowable cost per minute rather than an open-ended
one. Read "Security considerations" under Reference before you decide this
is enough for your situation.

Set a budget alert on the project anyway — defense in depth, not a
substitute for the above:

```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="cloud-run-renderer budget" \
  --budget-amount=10USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=1.0
```

A budget alert only notifies — it doesn't stop spend by itself. If you
want an actual kill-switch (a Cloud Function that disables billing or the
service past a threshold), that's separate infra this repo doesn't
include; search "GCP billing budget kill switch Cloud Function" for the
pattern.

*(If you specifically need the `/chat` webhook endpoint itself IAM-gated
instead of public, see "Alternative: IAM-gated deploy" below — it's a
two-service setup, more moving parts, and not the path most people want.)*

## Step 3 — Set up the Google Chat app

Two real gotchas before the steps, both confirmed against Google's own
current docs, not guessed:

**Gotcha #1 — you can end up building the wrong kind of thing entirely.**
Searching "build a Google Chat app/bot" surfaces Apps-Script-hosted
tutorials under *two different Google docs product lines* —
`developers.google.com/workspace/chat/quickstart/apps-script-app` and the
separate "Google Workspace add-ons" track,
`developers.google.com/workspace/add-ons/chat/...`. Both walk you through
writing Apps Script functions in an `appsscript.json`-manifested project —
neither one talks to a Cloud Run URL at all. This service is the *other*
kind: a plain HTTP endpoint, configured directly on the Chat API's own
Configuration page below. If a tutorial has you opening the Apps Script
editor, you're on the wrong path for this repo.

**Gotcha #2 — even on the right page, "Connection settings" has four
options and only one is correct here.** Per Google's own docs, the choices
are **HTTP endpoint URL**, **Apps Script project** (a Deployment ID),
**Cloud Pub/Sub Topic Name**, and **Dialogflow agent**. You want **HTTP
endpoint URL** — picking "Apps Script project" here is the same mistake as
Gotcha #1, just reachable from inside the correct page instead of a wrong
tutorial.

Now the steps:

1. In Google Cloud Console, on the **same project** you deployed to,
   enable the **Google Chat API**.
2. Go to **Google Chat API → Configuration**.
3. Fill in **App name**, **Avatar URL**, **Description** — whatever you
   want.
4. Under **Functionality**, enable "Receive 1:1 messages" and/or "Join
   spaces and group conversations", depending on where you want it usable.
5. Under **Connection settings** (see Gotcha #2), choose **HTTP endpoint
   URL** and paste `<your-service-url-from-step-2>/chat`.
6. Set `CHAT_AUDIENCE`. On a public deployment this is the *only* thing
   standing between `/chat` and anyone who finds the URL, so it is not
   optional — the route refuses every request until it is set.

   Chat signs every webhook POST with a bearer token issued by
   `chat@system.gserviceaccount.com`, and `_require_chat_caller()` in
   `server.py` verifies it. Which token you get depends on the
   **Authentication Audience** setting:

   | Authentication Audience | Audience value | Token type |
   |---|---|---|
   | App URL | `https://YOUR_SERVICE_URL/chat` | OIDC ID token |
   | Project Number | the **Chat app's** project number — the "Project number (App ID)" shown at the top of the config page, which is not necessarily the project this service runs in | JWT signed with Chat's x509 certs |

   **Your config page may not offer this setting.** Some Chat app
   configurations show only Connection settings, Triggers and Visibility,
   and Google's docs do not state which audience mode applies when the
   control is absent. `CHAT_AUDIENCE` therefore accepts a comma-separated
   list — set both values and the deployment is correct either way:

   ```
   CHAT_AUDIENCE=YOUR_CHAT_APP_PROJECT_NUMBER,https://YOUR_SERVICE_URL/chat
   ```

   Listing both weakens nothing: each names *your* app, so a token signed
   for a different Chat app matches neither. The service logs which
   audience verified (`chat auth: verified against audience '...'`), so
   you can narrow the list once you have seen it — though leaving both
   means a later console change won't take the app down.

   *(On the IAM-gated alternative below you can skip this: granting
   `chat@system.gserviceaccount.com` the `roles/run.invoker` role is
   Google's own documented complete answer for a Cloud Run target — "Cloud
   Run automatically handles token verification when you add the Google
   Chat service account as an authorized invoker". Setting `CHAT_AUDIENCE`
   anyway costs nothing and means the same code is safe in both modes. See
   [Verify requests from Google Chat](https://developers.google.com/workspace/chat/verify-requests-from-chat).)*
7. Under **Visibility**, restrict to specific people/groups, or your whole
   Workspace domain.
8. Save.

No Pub/Sub, no Apps Script project, no service account key to download —
the HTTP endpoint mode is the entire integration surface.

## Step 4 — Try it

Add the app to a space (or message it directly), then send:

- `intro` — a short spoken-style explainer of what this bot demonstrates.
- `workspace stats` — live Google Workspace service status.
- `weather` — a 3-day Toulouse forecast (real Open-Meteo data).
- `sla 82` — a standalone SLA gauge, useful for a first quick test.
- Add `gif` to any of the above (e.g. `weather gif`) to collapse the whole
  multi-card deck into one animated image.

If a command returns a card but the image is broken, the most likely cause
is Step 2's `--allow-unauthenticated` flag being missed — re-check the
deployed service's access setting before anything else.

---

## Reference

### Routes

- **`POST /render`** — the core primitive: one atom block in, one PNG out.
  Requires `X-Render-Token`.
- **`POST /render-deck`** — deck of blocks in, one animated GIF out. Same
  body convention, no URL-length ceiling. Requires `X-Render-Token`.
- **`GET /render.png`, `GET /render.gif`** — the same rendering, but as a
  plain GET a browser or Chat's own image widget can fetch directly (no
  body, no auth header). This is what makes Chat integration possible at
  all: Chat's `image` widget only ever does an anonymous GET on a URL. The
  `?b=` token carries an HMAC, so only URLs this service minted are honored.
- **`POST /chat`** — the Google Chat HTTP-endpoint handler used in Step 4.
  See `_HELP_TEXT`/`_INTRO_TEXT` in `server.py` for the exact command set.
  Requires a Chat-signed bearer token (Step 3, item 6).
- **`GET /deck`** — JSON sibling of `/chat` for a non-Chat caller (e.g. a
  Gemini Enterprise agent): runs the identical fetch-and-shape logic and
  hands back `/render.png`/`/render.gif`-ready encoded query strings,
  without rendering any pixels itself. Requires `X-Render-Token`.
- **`GET /status`** — liveness check, the one open route (not `/healthz` —
  Cloud Run's own infrastructure intercepts that exact path before it
  reaches the container).

Everything above lives in this one file/service. There used to be a
second, separate Cloud Run service in the loop purely to re-serve
`/render.png`/`/render.gif` publicly in front of an IAM-gated `/render` —
that split only existed because Cloud Run IAM is all-or-nothing per
service, so a same-service public route wasn't possible under that auth
mode. Folded in now: this one service serves the whole thing, as long as
it's deployed the way Step 2 describes.

**2026-07-26 change:** `/chat`'s image URLs now default to this service's
own host instead of a separate private one — if you maintain a fork or a
deployment that previously relied on the old hardcoded default, set
`AGENT_BASE_URL` explicitly to preserve the old behavior; a fresh
deployment needs nothing set.

### Security considerations

This service is a headless Chromium reachable from the public internet.
The threat model is **cost and abuse, not data** — it renders public data
into images and holds no user data or spendable credential. What an open
deployment hands an attacker is your compute (a Chromium farm billed to
you) and an image host on your domain.

Each safeguard below exists for one specific failure. None is optional.

| Safeguard | Prevents |
|---|---|
| `X-Render-Token` on `/render`, `/render-deck`, `/deck` | A stranger with the URL launching Chromium on your bill. Cloud Run's public/private switch is per *service*, so exposing the image routes for Chat would otherwise expose these too. |
| Header only — no `?t=` query fallback | The key reaching log storage. Cloud Run records full query strings, and this key also signs image URLs, so that leak would let an attacker mint valid ones. |
| HMAC signature on `?b=` image tokens | Forged or guessed image URLs. `/render.png` and `/render.gif` must answer anonymously for Chat's widget; the signature means only URLs this service minted ever render. |
| Bearer-token check on `/chat` | Anyone who finds the endpoint driving your Chat app. |
| `CHAT_AUDIENCE` match | A token Google Chat signed for a *different* Chat app being replayed against yours. Same role as the audience in Workload Identity Federation. |
| Fail-closed on unset `CHAT_AUDIENCE` | A missing config value silently disabling the check — the shape that leaves a "gated" service open. |
| `MAX_RENDER_WIDTH`, `MAX_DECK_BLOCKS`, `MAX_BLOCK_JSON_BYTES`, `MAX_CONTENT_LENGTH` | One oversized request consuming a whole instance. |
| `MAX_RENDERS_PER_MINUTE` | Sustained abuse running up unbounded cost over time. |
| `--max-instances` | Everything above being wrong. It is the bound that does not depend on any check behaving correctly. |

Three consequences worth knowing before you deploy:

**One secret does two jobs.** `RENDER_SIGNING_KEY` is both the HMAC key
for image tokens and the shared `X-Render-Token` value — one thing to
store and rotate rather than two, at the cost that leaking it does double
damage.

**Rotating it invalidates outstanding image URLs.** Existing
`/render.png` links, including ones already sitting in Chat messages,
stop verifying immediately. That is what makes rotation meaningful, but
it makes rotation a visible event: cards re-render on the next command,
anything pasted somewhere permanent will 403.

**`MAX_RENDERS_PER_MINUTE` is per-process, not global.** Cloud Run
answers load by adding instances, so the real ceiling is that value times
your instance count. A true global limit needs a shared store
(Redis/Memorystore). Set a billing budget as well — and note a budget
alert only notifies, it does not stop spend.

**What is deliberately not protected.** `/status` is open — it is a
liveness probe returning a constant. There is no per-caller rate
limiting, no audit of who rendered what, and no way to revoke one caller:
a shared secret is shared, so every holder is indistinguishable. If you
need per-caller identity, revocation and audit, use the IAM-gated deploy
below, where each caller presents its own Google identity.

**Local development.** The checks are always on and there is no bypass
flag, so what you exercise locally is what runs in production:

```bash
RENDER_SIGNING_KEY=dev-key python server.py
curl -H "X-Render-Token: dev-key" -X POST localhost:8080/render ...
```

Without the env var the service generates a random per-process key and
warns loudly — usable for `/status`, nothing else, and broken across a
multi-instance deployment.

### Alternative: IAM-gated deploy

Worth it when you want **per-caller identity** rather than one shared
secret: each caller presents its own Google identity, gets its own
revocable `roles/run.invoker` grant, and every call is logged against a
real principal. A shared token can do none of that. It is more moving
parts than Step 2, and it is how the original two-service split this code
was ported from worked.

The in-app checks stay on in this mode — the code does not branch on
deployment mode, so `RENDER_SIGNING_KEY` is still required and callers
still send `X-Render-Token`. That is deliberate: switching a deployment
between the two modes is a flag change, never a code change.

Deploy IAM-gated, and grant Chat's own calling identity invoker access so
its webhook POST still reaches `/chat`:

```bash
gcloud run deploy YOUR_SERVICE_NAME \
  --source . --project YOUR_PROJECT --region YOUR_REGION \
  --no-allow-unauthenticated \
  --set-secrets RENDER_SIGNING_KEY=render-signing-key:latest

gcloud run services add-iam-policy-binding YOUR_SERVICE_NAME \
  --project YOUR_PROJECT --region YOUR_REGION \
  --member="serviceAccount:chat@system.gserviceaccount.com" \
  --role="roles/run.invoker"
```

Then deploy a **second**, separate instance of this exact same code
`--allow-unauthenticated` (same command as Step 2, different
`YOUR_SERVICE_NAME`), and point the first instance's `AGENT_BASE_URL` env
var at the second instance's URL:

```bash
gcloud run services update YOUR_GATED_SERVICE_NAME \
  --project YOUR_PROJECT --region YOUR_REGION \
  --update-env-vars AGENT_BASE_URL=https://YOUR_PUBLIC_SERVICE_URL
```

Only the second, public instance's `/render.png`/`/render.gif` routes ever
get hit for images.

Both instances must share the **same** `RENDER_SIGNING_KEY` — the gated
one mints the `?b=` tokens, the public one verifies them, and a mismatch
shows up as "invalid or forged render token" on every image.

The second instance is no longer needed to keep the costly routes safe —
a single `--allow-unauthenticated` deployment is already guarded
route-by-route (Step 2). The split buys exactly one extra thing: it keeps
`POST /render` unreachable at the network layer, so the only surface a
stranger can connect to at all is the signature-checked image GET. Worth
it if you want that; not required.

### For the 5 SVG-only atoms

Atoms declared `chat_raster: svg` in `atoms/schema.yaml` skip headless
Chromium entirely and go through the pure-Python SVG rasterizer instead
(`renderers/svg_raster.py`, no browser needed). This service exists for
everything else — atoms that genuinely need real CSS/DOM layout.
