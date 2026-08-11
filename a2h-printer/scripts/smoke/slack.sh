#!/usr/bin/env bash
# scripts/smoke/slack.sh — round-trips POST /slack/command against a running
# instance of this package, computing a REAL Slack HMAC signature locally
# (pure openssl, no external dependency, no live Slack app needed) — see
# lib/slack-security.js's documented v0 scheme.
#
# Usage:
#   SLACK_SIGNING_SECRET=... ./scripts/smoke/slack.sh [base_url]
# base_url defaults to http://localhost:8080. The server under test must be
# started with the SAME SLACK_SIGNING_SECRET.
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
SECRET="${SLACK_SIGNING_SECRET:?set SLACK_SIGNING_SECRET to the same value the server was started with}"

pass=0
fail=0

sign_and_post() {
  local body="$1" ts sig base
  ts="$(date +%s)"
  base="v0:${ts}:${body}"
  sig="v0=$(printf '%s' "$base" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')"
  curl -s -o /tmp/smoke_slack_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/slack/command" \
    -H "X-Slack-Request-Timestamp: $ts" \
    -H "X-Slack-Signature: $sig" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data "$body"
}

check() {
  local desc="$1" expect_code="$2" got_code="$3" grep_for="${4:-}"
  if [[ "$got_code" != "$expect_code" ]]; then
    echo "FAIL: $desc — expected HTTP $expect_code, got $got_code"
    echo "  body: $(cat /tmp/smoke_slack_resp.json)"
    fail=$((fail+1))
    return
  fi
  if [[ -n "$grep_for" ]] && ! grep -q "$grep_for" /tmp/smoke_slack_resp.json; then
    echo "FAIL: $desc — HTTP $got_code but response didn't contain '$grep_for'"
    echo "  body: $(cat /tmp/smoke_slack_resp.json)"
    fail=$((fail+1))
    return
  fi
  echo "PASS: $desc"
  pass=$((pass+1))
}

# 1. whoami — valid signature, proves the HMAC scheme + owner-key extraction work.
BODY="token=x&team_id=T_SMOKE&team_domain=smoke&channel_id=C_SMOKE&channel_name=general&user_id=U_SMOKE&user_name=smoke&command=%2Fa2ui&text=whoami&api_app_id=A_SMOKE&response_url=https%3A%2F%2Fhooks.slack.test%2Fx"
code="$(sign_and_post "$BODY")"
check "whoami (valid signature)" 200 "$code" "T_SMOKE"

# 2. help — no text at all.
BODY="token=x&team_id=T_SMOKE&team_domain=smoke&channel_id=C_SMOKE&channel_name=general&user_id=U_SMOKE&user_name=smoke&command=%2Fa2ui&text=&api_app_id=A_SMOKE&response_url=https%3A%2F%2Fhooks.slack.test%2Fx"
code="$(sign_and_post "$BODY")"
check "help (empty text)" 200 "$code" "Usage"

# 3. list — proves storage round-trip reachable (empty is a valid, expected state).
BODY="token=x&team_id=T_SMOKE&team_domain=smoke&channel_id=C_SMOKE&channel_name=general&user_id=U_SMOKE&user_name=smoke&command=%2Fa2ui&text=list&api_app_id=A_SMOKE&response_url=https%3A%2F%2Fhooks.slack.test%2Fx"
code="$(sign_and_post "$BODY")"
check "list" 200 "$code"

# 4. Invalid signature must be rejected — the actual security property.
code="$(curl -s -o /tmp/smoke_slack_resp.json -w '%{http_code}' \
  -X POST "$BASE_URL/slack/command" \
  -H "X-Slack-Request-Timestamp: $(date +%s)" \
  -H 'X-Slack-Signature: v0=deadbeef' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data "$BODY")"
check "invalid signature rejected" 401 "$code"

# 5. Stale timestamp (>5min old) must be rejected even with a correctly
# computed signature — the replay-protection window in slack-security.js.
STALE_TS=$(( $(date +%s) - 400 ))
STALE_BASE="v0:${STALE_TS}:${BODY}"
STALE_SIG="v0=$(printf '%s' "$STALE_BASE" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')"
code="$(curl -s -o /tmp/smoke_slack_resp.json -w '%{http_code}' \
  -X POST "$BASE_URL/slack/command" \
  -H "X-Slack-Request-Timestamp: $STALE_TS" \
  -H "X-Slack-Signature: $STALE_SIG" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data "$BODY")"
check "stale timestamp rejected" 401 "$code"

rm -f /tmp/smoke_slack_resp.json
echo "---"
echo "slack.sh: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
