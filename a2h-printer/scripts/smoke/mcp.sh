#!/usr/bin/env bash
# scripts/smoke/mcp.sh — round-trips POST /mcp (save_reading -> list_readings
# -> owner-key isolation check) against a running instance. Fast regression
# check reused across every later phase — see the plan's own phased-build-
# order verify steps.
#
# v1.1: sends real JSON-RPC 2.0 envelopes ({jsonrpc,id,method:"tools/call",
# params:{name,arguments}}) instead of v1.0's flat {tool,args} shape — see
# README's "Upgrading to v1.1" section for the migration this mirrors. Every
# request past the bearer-token check now returns HTTP 200 with JSON-RPC
# semantics in the body: a failed tool call is a `result` with `isError:true`,
# never an HTTP 400/403/500 — see routes/mcp.js's two-tier error mapping.
#
# Usage:
#   MCP_AUTH_TOKEN=... ./scripts/smoke/mcp.sh [base_url]
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
TOKEN="${MCP_AUTH_TOKEN:?set MCP_AUTH_TOKEN to the same value the server was started with}"

pass=0
fail=0

# Builds a tools/call JSON-RPC envelope: rpc_call <tool_name> <arguments_json>
rpc_call() {
  local name="$1" args="$2"
  printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"%s","arguments":%s}}' "$name" "$args"
}

post() {
  local body="$1"
  curl -s -o /tmp/smoke_mcp_resp.json -w '%{http_code}' \
    -X POST "$BASE_URL/mcp" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    --data "$body"
}

# check_ok DESC HTTP_CODE GREP_FOR — expects HTTP 200 and no isError:true.
check_ok() {
  local desc="$1" got_code="$2" grep_for="${3:-}"
  if [[ "$got_code" != "200" ]]; then
    echo "FAIL: $desc — expected HTTP 200, got $got_code"
    echo "  body: $(cat /tmp/smoke_mcp_resp.json)"
    fail=$((fail+1))
    return
  fi
  if grep -q '"isError":true' /tmp/smoke_mcp_resp.json; then
    echo "FAIL: $desc — expected a successful tool result, got isError:true"
    echo "  body: $(cat /tmp/smoke_mcp_resp.json)"
    fail=$((fail+1))
    return
  fi
  if [[ -n "$grep_for" ]] && ! grep -q "$grep_for" /tmp/smoke_mcp_resp.json; then
    echo "FAIL: $desc — HTTP 200 but response didn't contain '$grep_for'"
    echo "  body: $(cat /tmp/smoke_mcp_resp.json)"
    fail=$((fail+1))
    return
  fi
  echo "PASS: $desc"
  pass=$((pass+1))
}

# check_tool_error DESC HTTP_CODE — expects HTTP 200 with isError:true (a
# valid MCP request whose tool execution failed for a real reason — NOT a
# JSON-RPC protocol error, see routes/mcp.js's two-tier error mapping).
check_tool_error() {
  local desc="$1" got_code="$2"
  if [[ "$got_code" != "200" ]]; then
    echo "FAIL: $desc — expected HTTP 200 (tool errors are isError:true results, not HTTP errors), got $got_code"
    echo "  body: $(cat /tmp/smoke_mcp_resp.json)"
    fail=$((fail+1))
    return
  fi
  if ! grep -q '"isError":true' /tmp/smoke_mcp_resp.json; then
    echo "FAIL: $desc — expected isError:true, got: $(cat /tmp/smoke_mcp_resp.json)"
    fail=$((fail+1))
    return
  fi
  echo "PASS: $desc"
  pass=$((pass+1))
}

# 1. Wrong bearer token must be rejected — the actual security property.
#    Auth happens BEFORE JSON-RPC parsing, so this is still a real HTTP 401.
code="$(curl -s -o /tmp/smoke_mcp_resp.json -w '%{http_code}' \
  -X POST "$BASE_URL/mcp" -H 'Authorization: Bearer wrong-token' \
  -H 'Content-Type: application/json' \
  --data "$(rpc_call list_readings '{"team_id":"T_SMOKE","user_id":"U_SMOKE"}')")"
if [[ "$code" != "401" ]]; then
  echo "FAIL: wrong bearer token rejected — expected HTTP 401, got $code"
  fail=$((fail+1))
else
  echo "PASS: wrong bearer token rejected"
  pass=$((pass+1))
fi

# 2. Missing owner-key args -> isError:true tool result, not a bare 400.
code="$(post "$(rpc_call list_readings '{}')")"
check_tool_error "missing owner-key args rejected" "$code"

# 3. save_reading against a Slack-shaped identity.
code="$(post "$(rpc_call save_reading '{"team_id":"T_SMOKE","user_id":"U_SMOKE","reading":{"title":"smoke test reading","payload_p":"x"}}')")"
check_ok "save_reading (Slack identity)" "$code" '"id"'
READING_ID="$(jq -r '.result.structuredContent.id' /tmp/smoke_mcp_resp.json)"

# 4. list_readings must see what was just saved.
code="$(post "$(rpc_call list_readings '{"team_id":"T_SMOKE","user_id":"U_SMOKE"}')")"
check_ok "list_readings sees the saved reading" "$code" "$READING_ID"

# 5. Teams-shaped identity is a SEPARATE store — must not see the Slack save.
code="$(post "$(rpc_call list_readings '{"tenant_id":"TEN_SMOKE","user_id":"U_SMOKE"}')")"
check_ok "Teams identity is isolated from Slack identity" "$code"
if grep -q "$READING_ID" /tmp/smoke_mcp_resp.json; then
  echo "FAIL: Teams-identity list_readings leaked the Slack-identity reading — owner-key isolation broken"
  fail=$((fail+1))
else
  echo "PASS: Teams/Slack owner-key isolation holds"
  pass=$((pass+1))
fi

# 6. delete_reading cleans up after itself.
code="$(post "$(rpc_call delete_reading "{\"team_id\":\"T_SMOKE\",\"user_id\":\"U_SMOKE\",\"ids\":[\"$READING_ID\"]}")")"
check_ok "delete_reading" "$code"

# 7. Real MCP protocol handshake — initialize declares capabilities.tools,
#    tools/list returns this deployment's 7 tools.
code="$(post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')"
check_ok "initialize declares capabilities.tools" "$code" '"capabilities":{"tools":{}}'

code="$(post '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}')"
check_ok "tools/list returns save_reading" "$code" '"save_reading"'

rm -f /tmp/smoke_mcp_resp.json
echo "---"
echo "mcp.sh: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
