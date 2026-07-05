#!/usr/bin/env python3
"""
A2UI vs OpenUI Lang — token efficiency benchmark.

Measures LLM output tokens required to express the same 7 UI scenarios in:
  • A2UI atom calls (this catalogue)
  • OpenUI Lang (.oui samples from github.com/thesysdev/openui)
  • YAML / Vercel JSON-Render / Thesys C1 JSON  (OpenUI's own baselines)

Usage:
    pip install tiktoken requests pyyaml
    python run_benchmark.py
    python run_benchmark.py --format table   # markdown table only
    python run_benchmark.py --format csv
"""

import argparse
import json
import sys
from pathlib import Path

import requests
import tiktoken
import yaml

from a2ui_mappings import SCENARIOS

# ── Encoder ────────────────────────────────────────────────────────────────
ENC = tiktoken.get_encoding("cl100k_base")

def tokens(text: str) -> int:
    return len(ENC.encode(text))

# ── Fetch OpenUI samples from GitHub ──────────────────────────────────────
BASE = "https://raw.githubusercontent.com/thesysdev/openui/main/benchmarks/samples"
EXTS = {"oui": ".oui", "yaml": ".yaml", "vercel": ".vercel.jsonl", "c1": ".c1.json"}

SCENARIO_NAMES = [
    "simple-table",
    "contact-form",
    "dashboard",
    "pricing-page",
    "chart-with-data",
    "e-commerce-product",
    "settings-panel",
]

def fetch_openui_samples() -> dict:
    """Download all OpenUI benchmark samples. Returns {scenario: {format: text}}."""
    cache_dir = Path(__file__).parent / ".openui_cache"
    cache_dir.mkdir(exist_ok=True)
    samples: dict = {}
    for name in SCENARIO_NAMES:
        samples[name] = {}
        for fmt, ext in EXTS.items():
            cache_file = cache_dir / f"{name}{ext}"
            if cache_file.exists():
                samples[name][fmt] = cache_file.read_text()
            else:
                url = f"{BASE}/{name}{ext}"
                r = requests.get(url, timeout=10)
                if r.ok:
                    cache_file.write_text(r.text)
                    samples[name][fmt] = r.text
                else:
                    samples[name][fmt] = ""
    return samples

# ── A2UI token count ───────────────────────────────────────────────────────
def a2ui_tokens(scenario: str) -> int:
    atoms = SCENARIOS.get(scenario, [])
    return tokens(json.dumps(atoms, separators=(",", ":")))

# ── Run ────────────────────────────────────────────────────────────────────
def run() -> list[dict]:
    print("Fetching OpenUI samples…", file=sys.stderr)
    openui = fetch_openui_samples()

    rows = []
    for name in SCENARIO_NAMES:
        s = openui[name]
        row = {
            "scenario":  name,
            "a2ui":      a2ui_tokens(name),
            "oui":       tokens(s.get("oui",    "")),
            "yaml":      tokens(s.get("yaml",   "")),
            "vercel":    tokens(s.get("vercel", "")),
            "c1":        tokens(s.get("c1",     "")),
        }
        # savings vs OpenUI Lang
        if row["oui"] > 0:
            row["a2ui_vs_oui_pct"] = round((row["oui"] - row["a2ui"]) / row["oui"] * 100, 1)
        else:
            row["a2ui_vs_oui_pct"] = None
        rows.append(row)
    return rows

# ── Formatting ─────────────────────────────────────────────────────────────
def fmt_markdown(rows: list[dict]) -> str:
    lines = [
        "| Scenario | A2UI | OpenUI Lang | YAML | Vercel | C1 JSON | A2UI vs OUI |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    totals = {k: 0 for k in ("a2ui","oui","yaml","vercel","c1")}
    for r in rows:
        pct = f"{r['a2ui_vs_oui_pct']:+.1f}%" if r["a2ui_vs_oui_pct"] is not None else "n/a"
        lines.append(
            f"| {r['scenario']} | {r['a2ui']} | {r['oui']} | {r['yaml']} "
            f"| {r['vercel']} | {r['c1']} | {pct} |"
        )
        for k in totals:
            totals[k] += r[k]
    # totals row
    if totals["oui"] > 0:
        total_pct = f"{(totals['oui']-totals['a2ui'])/totals['oui']*100:+.1f}%"
    else:
        total_pct = "n/a"
    lines.append(
        f"| **TOTAL** | **{totals['a2ui']}** | **{totals['oui']}** | **{totals['yaml']}** "
        f"| **{totals['vercel']}** | **{totals['c1']}** | **{total_pct}** |"
    )
    return "\n".join(lines)

def fmt_csv(rows: list[dict]) -> str:
    import csv, io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()

def fmt_verbose(rows: list[dict]) -> str:
    out = []
    for r in rows:
        pct = f"{r['a2ui_vs_oui_pct']:+.1f}%" if r["a2ui_vs_oui_pct"] is not None else "n/a"
        out.append(f"\n{'─'*60}")
        out.append(f"  {r['scenario']}")
        out.append(f"{'─'*60}")
        out.append(f"  A2UI atoms      : {r['a2ui']:>6} tokens")
        out.append(f"  OpenUI Lang     : {r['oui']:>6} tokens   ({pct} A2UI advantage)")
        out.append(f"  YAML baseline   : {r['yaml']:>6} tokens")
        out.append(f"  Vercel baseline : {r['vercel']:>6} tokens")
        out.append(f"  C1 JSON baseline: {r['c1']:>6} tokens")
    return "\n".join(out)

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["verbose", "table", "csv"], default="verbose")
    args = parser.parse_args()

    rows = run()

    if args.format == "table":
        print(fmt_markdown(rows))
    elif args.format == "csv":
        print(fmt_csv(rows))
    else:
        print(fmt_verbose(rows))
        print("\n\n" + fmt_markdown(rows))

        # summary insight
        total_a2ui = sum(r["a2ui"] for r in rows)
        total_oui  = sum(r["oui"]  for r in rows)
        total_yaml = sum(r["yaml"] for r in rows)
        print(f"\n### Summary")
        if total_oui:
            print(f"A2UI vs OpenUI Lang : {(total_oui-total_a2ui)/total_oui*100:+.1f}%")
        if total_yaml:
            print(f"A2UI vs YAML        : {(total_yaml-total_a2ui)/total_yaml*100:+.1f}%")
        print(f"\nNote: A2UI 'contact-form' and 'settings-panel' use approximate atom")
        print(f"mappings — A2UI has no native <Form>/<Switch> atom, so these figures")
        print(f"are conservative. A raw html_panel call would be ~15–40 tokens.")

if __name__ == "__main__":
    main()
