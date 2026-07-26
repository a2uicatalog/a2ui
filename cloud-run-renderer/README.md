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
python3 cloud-run-renderer/server.py
```

In another shell:

```bash
curl -X POST localhost:8080/render -H "Content-Type: application/json" \
  -d '{"block": {"type": "gauge_sla", "value": 82, "max_value": 100, "label": "P1 Incident SLA"}}' \
  -o out.png
```

Open `out.png` — you should see a real rendered gauge. There's no auth
check at all when running locally like this (auth is Cloud Run's own IAM
layer at the platform level once deployed, not an in-app token).

Now exercise the full `/chat` flow, without a real Chat app yet:

```bash
curl -X POST localhost:8080/chat -H "Content-Type: application/json" \
  -d '{"type": "MESSAGE", "message": {"text": "sla 82 gif"}}'
```

This returns a real `cardsV2` JSON payload. Copy the `imageUrl` out of it
and open that URL directly — it points back at this same local server, and
fetching it gives you the actual rendered GIF. If both of these worked,
the render engine is solid and everything left is deployment + Chat
configuration.

## Step 2 — Deploy to Cloud Run

Chat's `image` widget does an **anonymous** GET on whatever `imageUrl` you
give it — no bearer token, no signed-in identity, nothing. That's a hard
constraint from Google's side, not a choice made here, and it's why the
deploy command below uses `--allow-unauthenticated`.

One-time setup — create the Secret Manager secret the render tokens are
signed with (see "Signed render tokens" below for why this matters; a
deliberate one-time manual step, not scripted):

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

**Don't drop `--max-instances`.** There's no *secret* to leak here — this
service only ever reads public data — but every render launches a real
headless Chromium process, and `--allow-unauthenticated` means anyone with
the URL can trigger one. `--max-instances` is a hard ceiling on how many
of those can run at once, independent of anything else.

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

None of this makes the endpoint anything other than public — Chat's
`image` widget fetch is anonymous by Google's own design, and there's no
way around that for this specific integration. What it does do: an
attacker without a validly-signed token gets a cheap, instant rejection
instead of a real Chromium launch, and even sustained valid-shaped traffic
is bounded to a knowable cost per minute rather than an open-ended one.

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
6. Leave **Authentication Audience** at its default — it only matters if
   you're running the IAM-gated alternative below, and even then, granting
   `chat@system.gserviceaccount.com` the `roles/run.invoker` role is
   Google's own documented complete answer for a Cloud Run target: "Cloud
   Run automatically handles token verification when you add the Google
   Chat service account as an authorized invoker" (see
   [Verify requests from Google Chat](https://developers.google.com/workspace/chat/verify-requests-from-chat)).
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
- **`GET /render.png`, `GET /render.gif`** — the same rendering, but as a
  plain GET a browser or Chat's own image widget can fetch directly (no
  body, no auth header). This is what makes Chat integration possible at
  all: Chat's `image` widget only ever does an anonymous GET on a URL.
- **`POST /chat`** — the Google Chat HTTP-endpoint handler used in Step 4.
  See `_HELP_TEXT`/`_INTRO_TEXT` in `server.py` for the exact command set.
- **`GET /deck`** — JSON sibling of `/chat` for a non-Chat caller (e.g. a
  Gemini Enterprise agent): runs the identical fetch-and-shape logic and
  hands back `/render.png`/`/render.gif`-ready encoded query strings,
  without rendering any pixels itself.
- **`GET /status`** — liveness check (not `/healthz` — Cloud Run's own
  infrastructure intercepts that exact path before it reaches the
  container).

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

### Alternative: IAM-gated deploy

Only worth it if you specifically need the `/chat` webhook endpoint itself
gated rather than public — this is how the original two-service split
this code was ported from worked, and it's more moving parts than Step 2
for most people.

Deploy IAM-gated, and grant Chat's own calling identity invoker access so
its webhook POST still reaches `/chat`:

```bash
gcloud run deploy YOUR_SERVICE_NAME \
  --source . --project YOUR_PROJECT --region YOUR_REGION \
  --no-allow-unauthenticated

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

### For the 5 SVG-only atoms

Atoms declared `chat_raster: svg` in `atoms/schema.yaml` skip headless
Chromium entirely and go through the pure-Python SVG rasterizer instead
(`renderers/svg_raster.py`, no browser needed). This service exists for
everything else — atoms that genuinely need real CSS/DOM layout.
