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
import re
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
        ua = s.get("upstream_auth")
        if ua is not None:
            # A keyed upstream is a shared quota: name the secret, never hold it, and cache/limit by declaration.
            assert isinstance(ua, dict) and set(ua) <= {"secret", "header", "prefix"}, \
                f"{name}: upstream_auth takes only secret, header, prefix"
            assert re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", str(ua.get("secret", ""))), \
                f"{name}: upstream_auth.secret must be an UPPER_SNAKE secret name"
            hdr = ua.get("header", "Authorization")
            assert hdr == "Authorization" or re.fullmatch(r"X-[A-Za-z0-9-]{1,40}", str(hdr)), \
                f"{name}: upstream_auth.header must be Authorization or X-*"
            assert isinstance(ua.get("prefix", ""), str), f"{name}: upstream_auth.prefix must be a string"
            assert s["cache_ttl_s"] >= 3600, f"{name}: a source that spends an upstream credential must cache >= 3600s"
            if s["access"]["tier"] == "public":
                assert s["limits"]["per_ip_per_min"] <= 20, \
                    f"{name}: a public source that spends a credential must keep per_ip_per_min <= 20"
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
