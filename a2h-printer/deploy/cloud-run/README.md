# Deploying to Cloud Run

The core app (`../../src`) has no GCP dependency — this directory is the first-class,
ready-to-run deploy path for Cloud Run specifically. Other platforms (Fly.io, Render, a
bare VPS via `docker compose`, ...) work the same way in spirit: build the image, mount
a volume for `/data`, inject the three secrets as env vars. This is just the one with a
script already written.

## Prerequisites

- `gcloud` CLI, authenticated (`gcloud auth login`), with a project to deploy into.
- A Slack app already created (see the main README's "Slack app setup" — you need the
  signing secret and bot token before running this).

## Deploy

```sh
export PROJECT_ID=your-gcp-project
export SLACK_SIGNING_SECRET=...
export SLACK_BOT_TOKEN=xoxb-...
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)

./deploy.sh
```

Re-run any time you change code or want to rotate a secret — it's idempotent (creates
the bucket/secrets only if missing, updates secret versions and redeploys otherwise).

Then go back to your Slack app config and point the Slash Command / Interactivity
Request URLs at the service URL `deploy.sh` prints.

## What this script sets up, and why

- **A Cloud Storage bucket, mounted as a volume at `/data`.** Cloud Run's local disk
  doesn't survive a new revision — without this, every redeploy wipes all saved
  readings. See the main README's storage section for the alternative (accept that
  tradeoff, skip the bucket) if you'd rather have a truly single-resource deployment.
- **Secret Manager** for the three credentials, rather than plain `--set-env-vars` —
  Cloud Run env vars are visible in the console/API to anyone with read access to the
  service; Secret Manager at least puts them behind their own IAM boundary.
- **`--max-instances 1`** always, regardless of `MIN_INSTANCES` — SQLite is
  single-writer, and one workspace's traffic never needs more than one instance anyway.
- **`--allow-unauthenticated`** — required. Slack's servers can't satisfy Cloud Run's own
  IAM; the HMAC signature check on `/slack/*` (`src/lib/slack-security.js`) is what
  actually gates the public routes.

## `MIN_INSTANCES` — decide before you run this

Defaults to `0` ($0 idle cost; the first person to trigger the bot after any idle gap
may see a Slack timeout — see the main README for the full explanation). Set
`MIN_INSTANCES=1` before running `deploy.sh` for an always-warm instance (~$10/month) if
that risk isn't acceptable for your workspace.

```sh
MIN_INSTANCES=1 ./deploy.sh
```
