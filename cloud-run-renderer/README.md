# cloud-run-renderer

A headless "print any atom" render service. `scripts/printer.py`'s local
chromium path can already render any atom the catalogue knows to a PNG —
but only on a machine with a browser sitting open, which means only a
human running it deliberately, never an unattended agent or webhook. This
is that same rendering step, deployed as a real standing Cloud Run service
instead.

It renders. It does not post to Chat — the existing GAS owner-broker
(`_apiChatImage_` on the `gas-wired-renderer` deployment) already does that,
generically, over any PNG bytes. `scripts/printer.py` calls this service
(if configured) for the rendering step, then hands the bytes to that same
broker exactly as it always has.

For the 5 atoms declared `chat_raster: svg` in `atoms/schema.yaml`, none of
this runs — those go through the pure-Python SVG rasterizer instead
(`renderers/svg_raster.py`), which needs no browser at all. This service
exists for everything else: atoms that genuinely need real CSS/DOM layout.

## API

```
POST /render
  Authorization: Bearer <A2UI_RENDER_TOKEN>
  Content-Type: application/json
  Body: {"block": {...atom...}, "width": 620, "title": "", "subtitle": ""}

  -> 200, image/png bytes
  -> 400 {"ok": false, "error": "..."}   bad/unknown atom
  -> 401 {"ok": false, "error": "unauthorized"}   missing/wrong token
```

## Deploy

**The Dockerfile lives at the repo root** (`../Dockerfile` from here), not
in this directory — `gcloud run deploy --source` only auto-detects a
Dockerfile literally at the root of its source directory, and Docker won't
let a build `COPY` anything outside its context either way, so it has to
live where it can see `renderers/` (reused as-is — the exact same atom→HTML
code every other surface in this repo uses, not a second, drifting copy).
Deploy commands below run from the repo root.

One-time setup — create the Secret Manager secret holding the render
token (not scripted; a deliberate one-time manual step, same posture as
other credential setup in `ops/project-ops.yaml`):

```bash
echo -n "<pick a random token>" | gcloud secrets create a2ui-render-token \
  --project=828378723395 --data-file=-
```

Deploy via the declared process (never raw ad-hoc `gcloud`):

```bash
python3 ops/ops.py run cloud-run-renderer-deploy
```

Which runs (see `ops/project-ops.yaml`):

```bash
gcloud run deploy a2ui-atom-renderer \
  --source . \
  --project 828378723395 \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-secrets A2UI_RENDER_TOKEN=a2ui-render-token:latest
```

`--allow-unauthenticated` makes the URL publicly reachable — auth is the
app-level bearer token check in `server.py`, the same posture the GAS
owner-broker already uses (a token-gated anonymous endpoint), not Cloud
Run's IAM-based invoker auth.

## Local verification (no Docker required)

Playwright/chromium can run directly on the host — no container needed to
verify the render logic itself:

```bash
pip install -r cloud-run-renderer/requirements.txt
playwright install chromium
A2UI_RENDER_TOKEN=test python3 cloud-run-renderer/server.py
# in another shell:
curl -X POST localhost:8080/render \
  -H "Authorization: Bearer test" -H "Content-Type: application/json" \
  -d '{"block": {"type": "badge_group", "badges": [{"text": "live"}]}}' \
  -o out.png
```
