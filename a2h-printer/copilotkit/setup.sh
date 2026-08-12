#!/usr/bin/env bash
# setup.sh — guided install for CopilotKit Channels mode.
#
# Roast-panel finding, 2026-08-12: the README's 8-step install has real,
# unavoidable human touchpoints (browser login, a TUI project picker,
# creating a Slack app) — this script does NOT try to script those away.
# What it DOES do: run `npm install`/`.env` setup for you, write the one
# static value (INTELLIGENCE_GATEWAY_WS_URL) that has a known-correct
# answer instead of asking you to hand-copy it, and prompt you for exactly
# the two values only YOU can supply after each interactive CLI step
# completes (INTELLIGENCE_API_KEY, CHANNEL_CODE) — rather than sending you
# back to README.md to find where to paste them.
#
# Safe to re-run: never overwrites an existing .env, only appends missing
# keys to it.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "== a2h Printer — CopilotKit Channels mode setup =="
echo

# ── .env scaffold (idempotent) ──────────────────────────────────────────
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[scriptable] Created .env from .env.example."
else
  echo "[scriptable] .env already exists — leaving it as-is, will only APPEND missing keys below."
fi

set_env_if_missing() {
  local key="$1" value="$2"
  if grep -q "^${key}=" .env 2>/dev/null && [[ -n "$(grep "^${key}=" .env | cut -d= -f2-)" ]]; then
    return 0 # already set to a non-empty value, leave it alone
  fi
  if grep -q "^${key}=" .env 2>/dev/null; then
    # key exists but is empty — fill it in place
    local esc_value
    esc_value=$(printf '%s' "$value" | sed 's/[&/\]/\\&/g')
    sed -i "s|^${key}=.*|${key}=${esc_value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
  echo "[scriptable] Set ${key} in .env."
}

# ── npm install (scriptable) ────────────────────────────────────────────
echo
echo "[scriptable] Running npm install..."
npm install

# ── CopilotKit CLI (installing it is scriptable; login/select are not) ──
echo
if ! command -v copilotkit >/dev/null 2>&1; then
  echo "[scriptable] Installing the copilotkit CLI globally..."
  npm install -g copilotkit
fi

echo
echo "[human] Step 1/3: CopilotKit login (opens a browser)."
read -rp "    Press Enter to run 'npx copilotkit login'... "
npx copilotkit login

echo
echo "[human] Step 2/3: select or create a CopilotKit project (interactive TUI)."
read -rp "    Press Enter to run 'npx copilotkit project select'... "
npx copilotkit project select

echo
echo "[human] That step printed an INTELLIGENCE_API_KEY — paste it here (input hidden):"
read -rsp "    INTELLIGENCE_API_KEY: " intelligence_key
echo
if [[ -n "$intelligence_key" ]]; then
  set_env_if_missing INTELLIGENCE_API_KEY "$intelligence_key"
fi

# The one static, known-correct value the CLI doesn't provision itself
# (CopilotKit's own tracked CLI gap, OSS-714) — no need to ask a human for
# this, it's always the same.
set_env_if_missing INTELLIGENCE_GATEWAY_WS_URL "wss://realtime.intelligence.copilotkit.ai"

echo
echo "[human] Step 3/3: create the Slack app from CopilotKit's own CLI-generated"
echo "         manifest (do NOT create it from scratch on api.slack.com — see"
echo "         README.md for why)."
read -rp "    Press Enter to run 'npx copilotkit channels add --adapter slack'... "
npx copilotkit channels add --adapter slack

echo
echo "[human] That step asked you to name a channel — paste that same name here:"
read -rp "    CHANNEL_CODE: " channel_code
if [[ -n "$channel_code" ]]; then
  set_env_if_missing CHANNEL_CODE "$channel_code"
fi

echo
echo "== Remaining manual steps (see .env's own comments for each) =="
echo "  - GOOGLE_VERTEX_PROJECT / GOOGLE_VERTEX_LOCATION, if using the default"
echo "    vertex: model — plus 'gcloud auth application-default login' once."
echo "  - RENDER_SIGNING_KEY — reuse ../src/'s if you have a self-hosted"
echo "    deployment, or generate any 32+ byte random string otherwise."
echo
echo "Once .env is complete: npm run slack"
