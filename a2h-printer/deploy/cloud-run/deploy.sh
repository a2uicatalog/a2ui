#!/usr/bin/env bash
# deploy/cloud-run/deploy.sh — one-shot deploy for the a2uicatalog Slack
# Surface to Cloud Run. Idempotent: safe to re-run after a code change or a
# config tweak.
#
# The core app (../../src) is platform-agnostic — nothing in it imports a
# GCP SDK. Everything GCP-specific lives in this directory: bucket creation
# for durable SQLite storage, Secret Manager wiring, and the `gcloud run
# deploy` invocation itself. Read ../../README.md's "MIN_INSTANCES decision"
# section before running this — MIN_INSTANCES below defaults to the $0-idle
# option, not the always-warm one.
#
# Required env vars (set these, do NOT hardcode secrets into this file or
# commit them anywhere):
#   PROJECT_ID            gcloud project to deploy into
#   SLACK_SIGNING_SECRET   from Slack app's Basic Information page
#   SLACK_BOT_TOKEN         from Slack app's OAuth & Permissions page (xoxb-...)
#   MCP_AUTH_TOKEN          generate with: openssl rand -hex 32
#
# Also required, but with an explicit escape hatch each (see the two deploy-
# time guards below, added after a 2026-08-12 roast-panel pass):
#   MCP_ALLOWED_OWNERS — or set MCP_ALLOW_OPEN_IDENTITY=1 to proceed without
#                         one (e.g. a throwaway/demo deployment).
#   BUCKET_NAME + all four *_SECRET_NAME vars below — only when SERVICE_NAME
#                         is set to something other than the default; no
#                         escape hatch, this one's a real collision otherwise.
#
# Optional:
#   REGION                  default us-central1
#   SERVICE_NAME             default a2uicatalog-slack-surface
#   BUCKET_NAME              default ${PROJECT_ID}-slack-surface-data
#   SLACK_DEFAULT_CHANNEL    default #general
#   MIN_INSTANCES            default 0 — see README's cost/latency tradeoff
#   RENDER_BASE_URL          enables the D-bucket image fallback (atoms with
#                            no native Slack block) when set — the base URL
#                            of a live cloud-run-renderer deployment (e.g.
#                            https://a2ui-renderer-public-<hash>.a.run.app).
#                            Unset by default: D-bucket atoms then fail that
#                            message's whole compile, same as today.
#   RENDER_SIGNING_KEY_SECRET  name of the EXISTING Secret Manager secret
#                              holding that renderer's RENDER_SIGNING_KEY —
#                              reused, not recreated, so both services keep
#                              signing/verifying with the same key. Only
#                              read when RENDER_BASE_URL is set. Default:
#                              render-signing-key
#   SLACK_SIGNING_SECRET_NAME / SLACK_BOT_TOKEN_SECRET_NAME /
#   MCP_AUTH_TOKEN_SECRET_NAME / TEAMS_APP_PASSWORD_SECRET_NAME
#                              Secret Manager secret NAMES this run writes
#                              to — default to this script's original
#                              literals (slack-signing-secret, slack-bot-
#                              token, mcp-auth-token, teams-app-password),
#                              unchanged from every prior release. Override
#                              ALL FOUR (plus BUCKET_NAME below) with a
#                              distinct value whenever SERVICE_NAME differs
#                              from the default — running this script twice
#                              in ONE project with just a different
#                              SERVICE_NAME and no other overrides adds a
#                              new version to the SAME secrets the first
#                              service reads via :latest (silently rotating
#                              its live MCP_AUTH_TOKEN/Teams password out
#                              from under it) and mounts the SAME GCS bucket
#                              for SQLite from two concurrent Cloud Run
#                              services — exactly the concurrent-writer case
#                              README.md's own storage section says GCS-FUSE
#                              SQLite is unsafe for. Found live 2026-08-12
#                              standing up a second instance; these vars are
#                              the fix, mirroring RENDER_SIGNING_KEY_SECRET's
#                              already-existing override pattern above.
#   TEAMS_APP_ID / TEAMS_APP_PASSWORD  enables the Microsoft Teams surface
#                              when BOTH are set (README.md's "Teams app
#                              setup"). Unset by default: /api/messages then
#                              fails closed with a clear "not configured"
#                              error, same posture as RENDER_BASE_URL above.
#   TEAMS_AUTH_TENANT          default 'botframework.com' (MultiTenant Azure
#                              Bot registration) — only set this if you
#                              registered SingleTenant instead.
#   CHAT_AUDIENCE              enables the Google Chat surface when set — the
#                              "Authentication Audience" value(s) from the
#                              Chat API's Configuration page (this service's
#                              /chat URL, and/or a numeric project number;
#                              comma-separated if both). REQUIRES
#                              RENDER_BASE_URL too — Chat has no native block
#                              compiler, every atom needs the image-render
#                              fallback to display anything (see README).
#   TRUST_CLOUD_RUN_IAM         only relevant on a --no-allow-unauthenticated
#                              deployment (this script always deploys
#                              --allow-unauthenticated, so leave unset unless
#                              you've modified that) — see lib/chat-security.js.
#   CHAT_SERVICE_ACCOUNT        enables Chat PROACTIVE posting (an agent
#                              pushing content into a space via /mcp's
#                              render_reading_to_chat) with ZERO key file —
#                              the email of the service account REGISTERED
#                              AS THIS CHAT APP'S OWN IDENTITY in the Chat
#                              API configuration. This is NOT "any service
#                              account" — Chat's app-authenticated API
#                              requires that SPECIFIC one. Passed to `gcloud
#                              run deploy --service-account`, so Application
#                              Default Credentials resolve it automatically
#                              via the metadata server at runtime (see
#                              lib/chat-auth.js). Only needed for proactive
#                              posting — Chat's inbound webhook-reply
#                              (CHAT_AUDIENCE above) works without this.
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${SLACK_SIGNING_SECRET:?Set SLACK_SIGNING_SECRET}"
: "${SLACK_BOT_TOKEN:?Set SLACK_BOT_TOKEN}"
: "${MCP_AUTH_TOKEN:?Set MCP_AUTH_TOKEN}"

# Captured BEFORE any default is applied below — this is how the multi-
# instance guard (further down) tells "caller explicitly named a value"
# apart from "caller is using the default."
_SERVICE_NAME_WAS_SET="${SERVICE_NAME+x}"
_BUCKET_NAME_WAS_SET="${BUCKET_NAME+x}"
_SLACK_SIGNING_SECRET_NAME_WAS_SET="${SLACK_SIGNING_SECRET_NAME+x}"
_SLACK_BOT_TOKEN_SECRET_NAME_WAS_SET="${SLACK_BOT_TOKEN_SECRET_NAME+x}"
_MCP_AUTH_TOKEN_SECRET_NAME_WAS_SET="${MCP_AUTH_TOKEN_SECRET_NAME+x}"
_TEAMS_APP_PASSWORD_SECRET_NAME_WAS_SET="${TEAMS_APP_PASSWORD_SECRET_NAME+x}"

REGION="${REGION:-us-central1}"
# Kept as the original service name deliberately, even though the repo/package
# renamed to "a2h-printer" — renaming a LIVE service means re-pointing an
# already-configured Slack app's Request URLs / Azure Bot messaging endpoint,
# a separate deliberate operational step, not bundled into the code rename.
SERVICE_NAME="${SERVICE_NAME:-a2uicatalog-slack-surface}"
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-slack-surface-data}"
SLACK_DEFAULT_CHANNEL="${SLACK_DEFAULT_CHANNEL:-#general}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"
RENDER_BASE_URL="${RENDER_BASE_URL:-}"
RENDER_SIGNING_KEY_SECRET="${RENDER_SIGNING_KEY_SECRET:-render-signing-key}"
# See header comment above — override all four whenever SERVICE_NAME/
# BUCKET_NAME differ from the default, to avoid colliding with another
# instance's secrets in the same project.
SLACK_SIGNING_SECRET_NAME="${SLACK_SIGNING_SECRET_NAME:-slack-signing-secret}"
SLACK_BOT_TOKEN_SECRET_NAME="${SLACK_BOT_TOKEN_SECRET_NAME:-slack-bot-token}"
MCP_AUTH_TOKEN_SECRET_NAME="${MCP_AUTH_TOKEN_SECRET_NAME:-mcp-auth-token}"
TEAMS_APP_PASSWORD_SECRET_NAME="${TEAMS_APP_PASSWORD_SECRET_NAME:-teams-app-password}"
# Comma-separated slack:{team_id}:{user_id} the /mcp token may act for.
# Unset = permissive (any caller-asserted identity accepted, logged loudly).
# Set it: /mcp derives the storage key from caller-supplied args with nothing
# verifying the claim, so without this one token reads and writes EVERY
# identity's data. Find yours with the `/a2ui whoami` slash command.
MCP_ALLOWED_OWNERS="${MCP_ALLOWED_OWNERS:-}"
TEAMS_APP_ID="${TEAMS_APP_ID:-}"
TEAMS_APP_PASSWORD="${TEAMS_APP_PASSWORD:-}"
TEAMS_AUTH_TENANT="${TEAMS_AUTH_TENANT:-}"
CHAT_AUDIENCE="${CHAT_AUDIENCE:-}"
TRUST_CLOUD_RUN_IAM="${TRUST_CLOUD_RUN_IAM:-}"
CHAT_SERVICE_ACCOUNT="${CHAT_SERVICE_ACCOUNT:-}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ── Deploy-time guard #1: multi-instance secret/bucket collision ───────────
# Roast-panel finding, 2026-08-12: a deployer who overrides SERVICE_NAME but
# forgets even one of the four *_SECRET_NAME vars (or BUCKET_NAME) silently
# reproduces the exact collision this script's header comment already warns
# about — a comment is not a guard. This makes it structurally impossible
# instead: naming a non-default SERVICE_NAME REQUIRES every other override
# to also be explicit. Deploy-time only — does not touch any already-running
# service, since it only fires on a NEW invocation of this script.
if [[ -n "$_SERVICE_NAME_WAS_SET" && "$SERVICE_NAME" != "a2uicatalog-slack-surface" ]]; then
  _missing_overrides=()
  for _var in BUCKET_NAME SLACK_SIGNING_SECRET_NAME SLACK_BOT_TOKEN_SECRET_NAME \
              MCP_AUTH_TOKEN_SECRET_NAME TEAMS_APP_PASSWORD_SECRET_NAME; do
    _was_set_name="_${_var}_WAS_SET"
    if [[ -z "${!_was_set_name:-}" ]]; then
      _missing_overrides+=("$_var")
    fi
  done
  if [[ ${#_missing_overrides[@]} -gt 0 ]]; then
    echo "ERROR: SERVICE_NAME=${SERVICE_NAME} differs from the default, but the" >&2
    echo "       following overrides were NOT explicitly set: ${_missing_overrides[*]}" >&2
    echo "       Running with only SERVICE_NAME changed will write to the SAME" >&2
    echo "       Secret Manager secrets and GCS bucket the default-named service" >&2
    echo "       uses — silently rotating its live credentials and sharing its" >&2
    echo "       SQLite storage. Set all five explicitly (see this script's header" >&2
    echo "       comment for what each one does) before deploying a second instance." >&2
    exit 1
  fi
fi

# ── Deploy-time guard #2: /mcp identity gate must be an explicit choice ────
# Roast-panel finding, 2026-08-12: MCP_ALLOWED_OWNERS unset is a DELIBERATE
# runtime default (see the var's own comment above) — flipping it fail-
# closed at RUNTIME would silently break every already-deployed instance on
# next boot, the exact incident the runtime default was chosen to avoid.
# This is the other half: a NEW deploy must actively acknowledge running
# open, rather than getting there by never having read this far. Set
# MCP_ALLOWED_OWNERS for real, or set MCP_ALLOW_OPEN_IDENTITY=1 to proceed
# anyway (e.g. for a throwaway/demo deployment where this genuinely doesn't
# matter yet).
if [[ -z "$MCP_ALLOWED_OWNERS" && "${MCP_ALLOW_OPEN_IDENTITY:-}" != "1" ]]; then
  echo "ERROR: MCP_ALLOWED_OWNERS is unset. Without it, any holder of" >&2
  echo "       MCP_AUTH_TOKEN can read or write ANY identity's data via /mcp." >&2
  echo "       Set MCP_ALLOWED_OWNERS to a comma-separated allowlist (find" >&2
  echo "       yours with the /a2ui whoami slash command once Slack is live)," >&2
  echo "       or set MCP_ALLOW_OPEN_IDENTITY=1 to explicitly proceed without" >&2
  echo "       one anyway." >&2
  echo "" >&2
  echo "       Redeploying a service that was ALREADY LIVE and working before" >&2
  echo "       2026-08-12? This is a new safety gate, not a regression — that" >&2
  echo "       service has been running with this same permissive posture all" >&2
  echo "       along; MCP_ALLOW_OPEN_IDENTITY=1 keeps it working exactly as" >&2
  echo "       before while you decide whether to lock it down for real." >&2
  exit 1
fi

echo "==> Bucket for persistent SQLite storage (gs://${BUCKET_NAME})"
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" --project "$PROJECT_ID" --location "$REGION"
else
  echo "    already exists, skipping"
fi

echo "==> Secrets (Secret Manager)"
create_or_update_secret() {
  local name="$1" value="$2"
  if ! gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets create "$name" --project "$PROJECT_ID" --data-file=-
  else
    printf '%s' "$value" | gcloud secrets versions add "$name" --project "$PROJECT_ID" --data-file=-
  fi
}
create_or_update_secret "$SLACK_SIGNING_SECRET_NAME" "$SLACK_SIGNING_SECRET"
create_or_update_secret "$SLACK_BOT_TOKEN_SECRET_NAME" "$SLACK_BOT_TOKEN"
create_or_update_secret "$MCP_AUTH_TOKEN_SECRET_NAME" "$MCP_AUTH_TOKEN"
if [[ -n "$TEAMS_APP_ID" && -n "$TEAMS_APP_PASSWORD" ]]; then
  create_or_update_secret "$TEAMS_APP_PASSWORD_SECRET_NAME" "$TEAMS_APP_PASSWORD"
fi

echo "==> Granting the Cloud Run runtime service account access to these secrets"
# The default compute service account has no Secret Manager access on a
# fresh project — --set-secrets fails at deploy time without this. Grant is
# idempotent (add-iam-policy-binding no-ops if already present).
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
SECRETS_TO_GRANT=("$SLACK_SIGNING_SECRET_NAME" "$SLACK_BOT_TOKEN_SECRET_NAME" "$MCP_AUTH_TOKEN_SECRET_NAME")
SET_SECRETS="SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET_NAME}:latest,SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN_SECRET_NAME}:latest,MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN_SECRET_NAME}:latest"
SET_ENV_VARS="SLACK_DEFAULT_CHANNEL=${SLACK_DEFAULT_CHANNEL}"
if [[ -n "$MCP_ALLOWED_OWNERS" ]]; then
  echo "    /mcp identity gate ON — token may act only for: ${MCP_ALLOWED_OWNERS}"
  SET_ENV_VARS="${SET_ENV_VARS},MCP_ALLOWED_OWNERS=${MCP_ALLOWED_OWNERS}"
else
  echo "    WARNING: MCP_ALLOWED_OWNERS unset — /mcp will accept ANY caller-asserted identity"
fi
if [[ -n "$RENDER_BASE_URL" ]]; then
  echo "    RENDER_BASE_URL set — wiring the D-bucket image fallback (reusing secret: ${RENDER_SIGNING_KEY_SECRET})"
  SECRETS_TO_GRANT+=("$RENDER_SIGNING_KEY_SECRET")
  SET_SECRETS="${SET_SECRETS},RENDER_SIGNING_KEY=${RENDER_SIGNING_KEY_SECRET}:latest"
  SET_ENV_VARS="${SET_ENV_VARS},RENDER_BASE_URL=${RENDER_BASE_URL}"
fi
if [[ -n "$TEAMS_APP_ID" && -n "$TEAMS_APP_PASSWORD" ]]; then
  echo "    Teams surface ON — App ID: ${TEAMS_APP_ID}"
  SECRETS_TO_GRANT+=("$TEAMS_APP_PASSWORD_SECRET_NAME")
  SET_SECRETS="${SET_SECRETS},TEAMS_APP_PASSWORD=${TEAMS_APP_PASSWORD_SECRET_NAME}:latest"
  SET_ENV_VARS="${SET_ENV_VARS},TEAMS_APP_ID=${TEAMS_APP_ID}"
  if [[ -n "$TEAMS_AUTH_TENANT" ]]; then
    SET_ENV_VARS="${SET_ENV_VARS},TEAMS_AUTH_TENANT=${TEAMS_AUTH_TENANT}"
  fi
else
  echo "    Teams surface OFF (set TEAMS_APP_ID + TEAMS_APP_PASSWORD to enable)"
fi
if [[ -n "$CHAT_AUDIENCE" ]]; then
  if [[ -z "$RENDER_BASE_URL" ]]; then
    echo "ERROR: CHAT_AUDIENCE is set but RENDER_BASE_URL is not." >&2
    echo "       Chat has no native block compiler — every atom needs the image-render" >&2
    echo "       fallback too. Set RENDER_BASE_URL (and reuse RENDER_SIGNING_KEY_SECRET)" >&2
    echo "       to enable Chat, or unset CHAT_AUDIENCE to skip it for now." >&2
    exit 1
  fi
  echo "    Chat surface ON — audience(s): ${CHAT_AUDIENCE}"
  SET_ENV_VARS="${SET_ENV_VARS},CHAT_AUDIENCE=${CHAT_AUDIENCE}"
  if [[ -n "$TRUST_CLOUD_RUN_IAM" ]]; then
    SET_ENV_VARS="${SET_ENV_VARS},TRUST_CLOUD_RUN_IAM=${TRUST_CLOUD_RUN_IAM}"
  fi
else
  echo "    Chat surface OFF (set CHAT_AUDIENCE to enable — also needs RENDER_BASE_URL, Chat has no native compiler)"
fi
DEPLOY_EXTRA_FLAGS=()
if [[ -n "$CHAT_SERVICE_ACCOUNT" ]]; then
  echo "    Chat proactive posting ON — deploying with --service-account=${CHAT_SERVICE_ACCOUNT}"
  echo "    (must be the SA registered as this Chat app's own identity — see this script's header comment)"
  DEPLOY_EXTRA_FLAGS+=(--service-account "$CHAT_SERVICE_ACCOUNT")
else
  echo "    Chat proactive posting OFF (set CHAT_SERVICE_ACCOUNT to enable render_reading_to_chat via /mcp)"
fi
for secret in "${SECRETS_TO_GRANT[@]}"; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --project "$PROJECT_ID" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet >/dev/null
done

echo "==> Deploying ${SERVICE_NAME} (min-instances=${MIN_INSTANCES})"
gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --source "$REPO_ROOT" \
  --region "$REGION" \
  --allow-unauthenticated \
  --max-instances 1 \
  --min-instances "$MIN_INSTANCES" \
  --set-env-vars "$SET_ENV_VARS" \
  --set-secrets "$SET_SECRETS" \
  --add-volume "name=data,type=cloud-storage,bucket=${BUCKET_NAME}" \
  --add-volume-mount "volume=data,mount-path=/data" \
  "${DEPLOY_EXTRA_FLAGS[@]}"

echo "==> Done. Point your Slack app's Request URLs at the service URL printed above:"
echo "    Slash Command:  <url>/slack/command"
echo "    Interactivity:  <url>/slack/interactivity"
if [[ -n "$TEAMS_APP_ID" && -n "$TEAMS_APP_PASSWORD" ]]; then
  echo "    Teams messaging endpoint (set on the Azure Bot resource): <url>/api/messages"
fi
if [[ -n "$CHAT_AUDIENCE" ]]; then
  echo "    Chat HTTP endpoint (set on the Chat API's Configuration page): <url>/chat"
fi
