#!/usr/bin/env python3
"""Compile atoms/data-sources.yaml -> public/catalogue/data-sources-v1.json.

The declared network-access registry (sources, CSP connect domains, cache/
rate/egress budgets) in catalogue format: public, agent-readable, and the
single input for every consumer — the browser bundle inlines it
(gen_mcp_apps_bundle), the mcp-worker proxy table is synced from it
(a2ui-private side), and the Phase-2 ui:// resource derives its
csp.connectDomains from it. Editing the yaml and rerunning this is the ONLY
sanctioned way network access changes.
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "atoms" / "data-sources.yaml"
OUT = ROOT / "public" / "catalogue" / "data-sources-v1.json"


def build():
    decl = yaml.safe_load(SRC.read_text())
    assert decl.get("version") == 1
    assert decl.get("proxy_base", "").startswith("https://")
    for name, s in decl.get("sources", {}).items():
        for key in ("upstream", "cache_ttl_s", "limits", "consumers",
                    "min_client_refresh_s", "access"):
            assert key in s, f"data source '{name}' missing declared '{key}'"
        assert s["limits"].get("per_ip_per_min"), f"{name}: per_ip_per_min required"
        assert s["limits"].get("upstream_per_min"), f"{name}: upstream_per_min required"
        assert s["access"].get("tier") in ("public", "keyed", "user", "agent"), \
            f"{name}: access.tier must be a declared tier"
        assert s["access"].get("scope"), f"{name}: access.scope required"
    registry = {
        "catalogId": "a2ui-data-sources-v1",
        "version": decl["version"],
        "csp": decl["csp"],
        "proxy_base": decl["proxy_base"],
        "sources": decl["sources"],
    }
    return registry


def main():
    registry = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} — {len(registry['sources'])} declared sources")


if __name__ == "__main__":
    main()
