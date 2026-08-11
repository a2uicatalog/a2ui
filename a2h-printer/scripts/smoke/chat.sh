#!/usr/bin/env bash
# scripts/smoke/chat.sh — exercises POST /chat against a running instance.
# Chat's REAL inbound auth is a live Google-signed bearer token verified
# against Google's own certs (see lib/chat-security.js) — that can't be
# manufactured locally without a real Chat app registration, so (mirroring
# scripts/smoke/teams.sh) this tests two offline-verifiable things:
#   1. The auth gate rejects requests when no bypass is armed.
#   2. With CHAT_DEV_BYPASS_AUTH=1 armed on the server (dev-only,
#      structurally inert outside NODE_ENV!=='production'), a request
#      reaches the handler and gets a real reply — proven with a `list`
#      command, which needs no render config to fail cleanly and no
#      outbound network call (unlike `show`/`weather`, which need
#      RENDER_SIGNING_KEY/RENDER_BASE_URL to produce a real card).
#
# Usage:
#   ./scripts/smoke/chat.sh [base_url] [--bypass-armed]
# Pass --bypass-armed if (and only if) YOU started the server under test
# with CHAT_DEV_BYPASS_AUTH=1 — see teams.sh's header comment for why this
# can't be auto-detected from the calling shell's own environment.
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
  local desc="$1" expect_code="$2" got_code="$3" grep_for="${4:-}"
  if [[ "$got_code" != "$expect_code" ]]; then
    echo "FAIL: $desc — expected HTTP $expect_code, got $got_code"
    echo "  body: $(cat /tmp/smoke_chat_resp.json)"
    fail=$((fail+1))
    return
  fi
  if [[ -n "$grep_for" ]] && ! grep -q "$grep_for" /tmp/smoke_chat_resp.json; then
    echo "FAIL: $desc — HTTP $got_code but response didn't contain '$grep_for'"
    echo "  body: $(cat /tmp/smoke_chat_resp.json)"
    fail=$((fail+1))
    return
  fi
  echo "PASS: $desc"
  pass=$((pass+1))
}

BODY="$(jq '.message.argumentText = "whoami"' "$FIXTURE_DIR/chat-event.json")"

if [[ "$BYPASS_ARMED" -eq 0 ]]; then
  # 1. No Authorization header, no bypass armed -> must reject. Real code
  # path, no live credentials needed. (If the server also has no render
  # config set, it 501s before even checking auth — either 403 or 501 here
  # proves the request never reached command logic unauthenticated; only a
  # bare 200 would be a real failure.)
  code="$(curl -s -o /tmp/smoke_chat_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/chat" -H 'Content-Type: application/json' --data "$BODY")"
  if [[ "$code" == "403" || "$code" == "501" ]]; then
    echo "PASS: no bearer, no bypass -> rejected (HTTP $code)"
    pass=$((pass+1))
  else
    echo "FAIL: no bearer, no bypass -> expected 403 or 501, got $code"
    echo "  body: $(cat /tmp/smoke_chat_resp.json)"
    fail=$((fail+1))
  fi
else
  # 2. Bypass armed server-side + `whoami` -> reaches the handler, replies
  # with the space/user identity. Needs CHAT_AUDIENCE set (for the 501
  # config-presence gate) but NOT a real render config, since whoami never
  # touches render-to-chat.js.
  code="$(curl -s -o /tmp/smoke_chat_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/chat" \
    -H 'Authorization: Bearer dummy-ignored-when-bypassed' \
    -H 'Content-Type: application/json' \
    --data "$BODY")"
  check "bypass armed, whoami -> reaches handler, identifies caller" 200 "$code" "SMOKE_SPACE"
fi

rm -f /tmp/smoke_chat_resp.json
echo "---"
echo "chat.sh: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
