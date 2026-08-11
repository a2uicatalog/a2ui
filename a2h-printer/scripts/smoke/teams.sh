#!/usr/bin/env bash
# scripts/smoke/teams.sh — exercises POST /api/messages against a running
# instance. Teams' REAL inbound auth is a live Bot Framework JWT verified
# against Bot Framework's own JWKS (see teams-security.js) — that can't be
# manufactured locally without a real Azure Bot registration, so this script
# tests two things that ARE fully offline-verifiable:
#   1. The auth gate rejects requests when no bypass is armed (the actual
#      security property — no live credentials needed to prove this).
#   2. With TEAMS_DEV_BYPASS_AUTH=1 armed on the server (dev-only, see
#      config.js/teams-security.js — structurally inert outside
#      NODE_ENV!=='production'), a request reaches the handler and the
#      envelope-validation logic runs — proven by omitting `serviceUrl` from
#      the fixture, which makes the handler return a clean 200 WITHOUT
#      attempting an outbound reply (avoiding a real network call to
#      Microsoft's OAuth endpoint, which needs real TEAMS_APP_ID/PASSWORD
#      this script deliberately does not have).
# A full round-trip (a real reply actually posted back into Teams) needs a
# live Azure Bot registration and is NOT what this script proves — see the
# plan's phase 7 note on Chat/Teams' live-infra-dependent verification.
#
# Usage:
#   ./scripts/smoke/teams.sh [base_url] [--bypass-armed]
# Pass --bypass-armed if (and only if) YOU started the server under test with
# TEAMS_DEV_BYPASS_AUTH=1 — this cannot be auto-detected from the calling
# shell's own environment (a background server process has its own launch
# env, which this script has no way to read), so it must be told explicitly
# rather than guessed. Without the flag, this script exercises the
# no-bypass rejection path (401); with it, the bypass-reaches-handler path
# (200 on a safe/serviceUrl-less envelope). Run it twice, once per server
# config, for full coverage — the two are mutually exclusive server states,
# not two things one server instance can prove at once.
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
BYPASS_ARMED=0
for arg in "$@"; do
  [[ "$arg" == "--bypass-armed" ]] && BYPASS_ARMED=1
done
FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixtures"

pass=0
fail=0

check() {
  local desc="$1" expect_code="$2" got_code="$3"
  if [[ "$got_code" != "$expect_code" ]]; then
    echo "FAIL: $desc — expected HTTP $expect_code, got $got_code"
    echo "  body: $(cat /tmp/smoke_teams_resp.json)"
    fail=$((fail+1))
    return
  fi
  echo "PASS: $desc"
  pass=$((pass+1))
}

BODY="$(jq '.text = "whoami" | del(.serviceUrl)' "$FIXTURE_DIR/teams-message.json")"

if [[ "$BYPASS_ARMED" -eq 0 ]]; then
  # 1. No Authorization header, no bypass armed -> must reject. This is the
  # actual security property: the real code path, no live credentials needed.
  code="$(curl -s -o /tmp/smoke_teams_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/api/messages" -H 'Content-Type: application/json' --data "$BODY")"
  check "no bearer, no bypass -> rejected" 401 "$code"
else
  # 2. Bypass armed server-side + envelope missing serviceUrl -> clean 200,
  # no outbound network call attempted (the safe, fully-offline path).
  code="$(curl -s -o /tmp/smoke_teams_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/api/messages" \
    -H 'Authorization: Bearer dummy-ignored-when-bypassed' \
    -H 'Content-Type: application/json' \
    --data "$BODY")"
  check "bypass armed, safe envelope -> reaches handler, clean 200" 200 "$code"
fi

rm -f /tmp/smoke_teams_resp.json
echo "---"
echo "teams.sh: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
