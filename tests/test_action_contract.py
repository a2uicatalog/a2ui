"""Lock the server response envelope {ok, data?, total?, error?} declared in
spec/gas-actions-v1.yaml (server_response_contract).

Every _action* handler in the wired renderer must return the envelope on
some path (presence check — nested map() returns are legitimately bare),
and the client runtime must keep the exact r.data -> result mapping the
contract documents. The 2026-07-02 silent-empty-dashboard incident is the
failure mode: an un-enveloped return copies undefined into node.result.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
CODE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "Code.gs"
STATE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "A2UIState.html"
PRIVATE_CODE = ROOT / ".." / "a2ui-private" / "gas-trade-bot" / "Code.gs"
SPEC = yaml.safe_load((ROOT / "spec" / "gas-actions-v1.yaml").read_text())


def _handlers_missing_ok(path):
    funcs = re.split(r"\nfunction ", path.read_text())
    return [f.split("(")[0].strip() for f in funcs
            if f.split("(")[0].strip().startswith("_action") and "ok:" not in f]


def _runtime_action_surface():
    """(output props set in _initAction, has _run input) from the runtime."""
    s = STATE.read_text()
    i = s.index("_initAction = function")
    j = s.index("this.nodes[p.id] = node;", i)
    body = s[i:j]
    outputs = set(re.findall(r"self\._set\(p\.id,\s*'([a-zA-Z]+)'", body))
    return outputs, ("_run = function" in body)


def test_spec_declares_the_envelope():
    spec = yaml.safe_load((ROOT / "spec" / "gas-actions-v1.yaml").read_text())
    c = spec.get("server_response_contract")
    assert c, "spec/gas-actions-v1.yaml lost its server_response_contract block"
    for k in ("ok", "data", "total", "error", "client_mapping"):
        assert k in c, f"server_response_contract missing field doc: {k}"


def test_every_wired_handler_returns_the_envelope():
    missing = _handlers_missing_ok(CODE)
    assert not missing, (
        f"handler(s) with no 'ok:' return in gas-wired-renderer: {missing} — "
        "every _action* must return the {ok, data, total, error} envelope "
        "(spec/gas-actions-v1.yaml server_response_contract)"
    )


def test_client_mapping_matches_contract():
    src = STATE.read_text()
    assert re.search(r"'result',\s*r\.data", src), (
        "A2UIState.html no longer copies r.data into node.result — update "
        "spec/gas-actions-v1.yaml client_mapping if this change is intentional"
    )
    assert re.search(r"r\.total\s*!==\s*undefined", src), (
        "A2UIState.html lost the r.total fallback documented in the contract"
    )


@pytest.mark.skipif(not PRIVATE_CODE.exists(),
                    reason="private sibling repo not present")
def test_every_trade_bot_handler_returns_the_envelope():
    missing = _handlers_missing_ok(PRIVATE_CODE)
    assert not missing, (
        f"handler(s) with no 'ok:' return in gas-trade-bot: {missing}"
    )


# ── ActionNode wiring contract (the addressable surface) ───────────────────

def test_action_node_contract_declared():
    an = SPEC.get("action_node")
    assert an, "spec lost the action_node contract block"
    for k in ("inputs", "outputs", "invocation"):
        assert k in an, f"action_node missing {k}"
    assert "run" in an["inputs"], "action_node.inputs must document the run trigger"


def test_documented_outputs_match_runtime():
    """Every documented output prop must actually be set by _initAction, and
    vice-versa — no drift between the contract and the runtime it describes."""
    runtime_outputs, has_run = _runtime_action_surface()
    doc_outputs = set(SPEC["action_node"]["outputs"].keys())
    assert has_run, "_initAction no longer defines node._run — run input is the contract's entry point"
    assert doc_outputs == runtime_outputs, (
        f"ActionNode output drift — documented {sorted(doc_outputs)} vs "
        f"runtime {sorted(runtime_outputs)}; reconcile spec/gas-actions-v1.yaml "
        "action_node.outputs with A2UIStateEngine._initAction"
    )


def test_reference_example_wires_only_documented_props():
    """payloads/expenses-demo.json is the worked reference — its wires into
    action nodes must reference only documented props (no reverse-engineering)."""
    import json
    demo = json.loads((ROOT / "payloads" / "expenses-demo.json").read_text())
    act_ids = {a["id"] for a in demo.get("actions", [])}
    addressable = set(SPEC["action_node"]["outputs"]) | set(SPEC["action_node"]["inputs"])
    bad = []
    for el in demo.get("layout", []):
        for expr in (el.get("wire") or {}).values():
            m = re.match(r"#(\w+)\.(\w+)$", str(expr))
            if m and m.group(1) in act_ids and m.group(2) not in addressable:
                bad.append(f"{el.get('id')}: {expr}")
    assert not bad, f"expenses-demo wires undocumented action props: {bad}"
