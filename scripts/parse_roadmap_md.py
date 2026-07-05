#!/usr/bin/env python3
"""
Deterministic roadmap.md → a2ui_wired_surface payload parser.

Implements spec/roadmap-md-v0.1.md — second instance of the
intermediate-MD-spec class (training.md was the first). No LLM anywhere:
content comes from the MD file; machinery (jump_nav, roadmap_card
overview, per-phase matrix tables) is derived by fixed rules.

Usage:
  python3 scripts/parse_roadmap_md.py <file.md> [-o out.json] [--report]

Exit codes: 0 ok, 2 lint errors (payload not emitted).
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")

REQUIRED_FRONTMATTER = ["id", "domain", "name", "source", "license"]
OPTIONAL_FRONTMATTER = ["horizon", "velocity_basis", "as_of"]
FORBIDDEN_FRONTMATTER = ["render", "layout", "atoms", "theme", "accent"]
ITEM_KEYS = ["status", "below", "above", "unlocks", "note"]
STATUSES = ["done", "in-progress", "planned"]
RISK_LEVELS = ["critical", "high", "medium", "low"]
KNOWN_SECTIONS = ["Phases", "Timeline", "Backlog", "Risks"]
STATUS_CLASSES = {"status-shipped": "shipped", "status-active": "active",
                  "status-designed": "designed", "status-planned": "planned"}

HEADING_ATTR_RE = re.compile(r"\s*\{([^}]*)\}\s*$")
ITEM_HEAD_RE = re.compile(r"^(\d+)\.\s+(.*)$")
ITEM_KEY_RE = re.compile(r"^([a-z_]+):\s?(.*)$")
CHECKBOX_RE = re.compile(r"^- \[([ xX])\]\s+(.*)$")
FENCE_RE = re.compile(r"^```(?:markdown)?\s*$")


class Lint:
    def __init__(self):
        self.errors, self.warnings = [], []

    def e(self, code, msg):
        self.errors.append(f"{code}: {msg}")

    def w(self, code, msg):
        self.warnings.append(f"{code}: {msg}")


def _strip_fence(text):
    lines = text.strip().splitlines()
    if lines and FENCE_RE.match(lines[0]) and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


def _parse_attrs(heading):
    attrs = {"hint": None, "cls": []}
    m = HEADING_ATTR_RE.search(heading)
    if not m:
        return heading.strip(), attrs
    title = heading[: m.start()].strip()
    for tok in m.group(1).split():
        if tok.startswith("#"):
            attrs["hint"] = tok[1:]
        elif tok.startswith("."):
            attrs["cls"].append(tok[1:])
    return title, attrs


def _split_sections(body_lines, lint):
    """Return (intro_lines, ordered {section: lines})."""
    intro, sections, current = [], {}, None
    for ln in body_lines:
        if ln.startswith("# "):
            name, _ = _parse_attrs(ln[2:])
            if name not in KNOWN_SECTIONS:
                lint.e("E04", f"unknown section heading '# {name}'")
            current = name
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(ln)
        else:
            intro.append(ln)
    return intro, sections


def _parse_phases(lines, lint):
    phases, phase = [], None
    for ln in lines:
        if ln.startswith("## "):
            title, attrs = _parse_attrs(ln[3:])
            status = "planned"
            for c in attrs["cls"]:
                if c in STATUS_CLASSES:
                    status = STATUS_CLASSES[c]
                else:
                    lint.w("W02", f"unknown status class '.{c}' on phase '{title}'")
            phase = {"title": title, "status": status, "summary": [], "items": []}
            phases.append(phase)
            continue
        if phase is None:
            if ln.strip():
                lint.e("E03", f"content before first '## phase' heading: {ln.strip()[:60]}")
            continue
        m = ITEM_HEAD_RE.match(ln.strip()) if not ln.startswith((" ", "\t")) else None
        if m:
            phase["items"].append({"title": m.group(2).strip(), "kv": {}})
            continue
        if ln.startswith((" ", "\t")) and phase["items"]:
            km = ITEM_KEY_RE.match(ln.strip())
            if km:
                key, val = km.group(1), km.group(2).strip()
                if key not in ITEM_KEYS:
                    lint.e("E05", f"unknown item key '{key}:' under "
                                  f"'{phase['items'][-1]['title']}'")
                else:
                    phase["items"][-1]["kv"][key] = val
                continue
            # continuation line of the previous value
            kv = phase["items"][-1]["kv"]
            if kv:
                last = list(kv)[-1]
                kv[last] += " " + ln.strip()
            continue
        if ln.strip():
            phase["summary"].append(ln.strip())
    for ph in phases:
        for it in ph["items"]:
            st = it["kv"].get("status")
            if st not in STATUSES:
                lint.e("E06", f"item '{it['title']}' has "
                              f"{'missing' if st is None else 'invalid'} status"
                              f"{'' if st is None else ' ' + repr(st)}")
    if not phases or not any(ph["items"] for ph in phases):
        lint.e("E03", "'# Phases' missing, empty, or has no items")
    return phases


def _parse_sep_bullets(lines, lint, section, min_fields, max_fields):
    out = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("- "):
            continue
        fields = [f.strip() for f in s[2:].split("::")]
        if len(fields) < min_fields:
            lint.e("E04", f"{section}: bullet needs at least {min_fields} "
                          f"'::' fields: {s[:60]}")
            continue
        out.append(fields[:max_fields])
    return out


def _parse_backlog(lines, lint):
    out = []
    for ln in lines:
        s = ln.strip()
        m = CHECKBOX_RE.match(s)
        if m:
            out.append({"text": m.group(2).strip(), "done": m.group(1) in "xX"})
        elif s.startswith("- "):
            out.append({"text": s[2:].strip(), "done": False})
    return out


def parse(text):
    lint = Lint()
    text = _strip_fence(text)
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        lint.e("E01", "missing YAML frontmatter block")
        return None, lint, {}
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as err:
        lint.e("E01", f"frontmatter is not valid YAML: {err}")
        return None, lint, {}
    for k in REQUIRED_FRONTMATTER:
        if not fm.get(k):
            lint.e("E01", f"missing required frontmatter key '{k}'")
    if fm.get("domain") not in (None, "roadmap"):
        lint.e("E01", f"domain must be 'roadmap', got '{fm.get('domain')}'")
    for k in FORBIDDEN_FRONTMATTER:
        if k in fm:
            lint.e("E02", f"forbidden frontmatter key '{k}' — presentation "
                          "lives in the parser")
    unknown = set(fm) - set(REQUIRED_FRONTMATTER) - set(OPTIONAL_FRONTMATTER)
    for k in sorted(unknown):
        lint.w("W01", f"unknown frontmatter key '{k}' (ignored)")

    intro, sections = _split_sections(m.group(2).splitlines(), lint)
    parsed = {"fm": fm, "intro": " ".join(l.strip() for l in intro if l.strip())}
    parsed["phases"] = _parse_phases(sections.get("Phases", []), lint)
    parsed["timeline"] = _parse_sep_bullets(
        sections.get("Timeline", []), lint, "Timeline", 2, 3)
    parsed["backlog"] = _parse_backlog(sections.get("Backlog", []), lint)
    parsed["risks"] = []
    for f in _parse_sep_bullets(sections.get("Risks", []), lint, "Risks", 2, 4):
        if f[0] not in RISK_LEVELS:
            lint.e("E07", f"invalid risk level '{f[0]}' (must be one of "
                          f"{'|'.join(RISK_LEVELS)})")
            continue
        risk = {"level": f[0], "title": f[1]}
        if len(f) > 2 and f[2]:
            risk["description"] = f[2]
        if len(f) > 3 and f[3]:
            risk["mitigation"] = f[3]
        parsed["risks"].append(risk)
    for sec in ("Timeline", "Backlog", "Risks"):
        if sec not in sections:
            lint.w("W03", f"optional section '# {sec}' absent")
    return parsed, lint, sections


def _slug(text):
    s = re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", s) or "x"


ITEM_STATUS_TO_CARD = {"done": "done", "in-progress": "in-progress",
                       "planned": "planned"}
PHASE_STATUS_LABEL = {"shipped": "SHIPPED", "active": "IN PROGRESS",
                      "designed": "DESIGNED", "planned": "PLANNED"}


def emit(parsed):
    fm = parsed["fm"]
    layout = [{"id": "title-heading", "atom": "subheading",
               "props": {"text": fm["name"]}}]
    nav_links, phase_heads = [], []
    for ph in parsed["phases"]:
        hid = f"phase-{_slug(ph['title'])}-heading"
        phase_heads.append(hid)
        nav_links.append({"label": ph["title"], "target": hid})
    if parsed["timeline"]:
        nav_links.append({"label": "Timeline", "target": "timeline-heading"})
    if parsed["backlog"]:
        nav_links.append({"label": "Backlog", "target": "backlog-heading"})
    if parsed["risks"]:
        nav_links.append({"label": "Risks", "target": "risks-heading"})
    layout.append({"id": "nav", "atom": "jump_nav", "props": {"links": nav_links}})
    if parsed["intro"]:
        layout.append({"id": "intro", "atom": "body",
                       "props": {"text": parsed["intro"]}})

    # Overview roadmap_card — periods = phases
    periods = []
    for ph in parsed["phases"]:
        label = ph["title"]
        tag = PHASE_STATUS_LABEL.get(ph["status"])
        if tag:
            label += f" — {tag}"
        periods.append({"label": label,
                        "items": [{"text": it["title"],
                                   "status": ITEM_STATUS_TO_CARD[it["kv"]["status"]]}
                                  for it in ph["items"]]})
    layout.append({"id": "overview", "atom": "roadmap_card",
                   "props": {"title": "Capability phases", "periods": periods}})
    layout.append({"id": "div-overview", "atom": "divider"})

    # Per-phase heading + summary + matrix table
    for i, ph in enumerate(parsed["phases"]):
        layout.append({"id": phase_heads[i], "atom": "subheading",
                       "props": {"text": ph["title"]}})
        if ph["summary"]:
            layout.append({"id": f"phase-{i}-summary", "atom": "body",
                           "props": {"text": " ".join(ph["summary"])}})
        rows = [[it["title"], it["kv"].get("below", ""),
                 it["kv"].get("above", ""), it["kv"]["status"],
                 it["kv"].get("unlocks", "")] for it in ph["items"]]
        layout.append({"id": f"phase-{i}-matrix", "atom": "data_table_sortable",
                       "props": {"headers": ["Item", "Below the surface",
                                             "Above the surface", "Status",
                                             "Unlocks"],
                                 "rows": rows}})
        notes = [f"{it['title']}: {it['kv']['note']}"
                 for it in ph["items"] if it["kv"].get("note")]
        if notes:
            layout.append({"id": f"phase-{i}-notes", "atom": "body",
                           "props": {"text": "  |  ".join(notes)}})
        layout.append({"id": f"div-phase-{i}", "atom": "divider"})

    if parsed["timeline"]:
        layout.append({"id": "timeline-heading", "atom": "subheading",
                       "props": {"text": "Timeline"}})
        events = []
        for f in parsed["timeline"]:
            ev = {"date": f[0], "title": f[1]}
            if len(f) > 2 and f[2]:
                ev["desc"] = f[2]
            events.append(ev)
        vb = fm.get("velocity_basis")
        props = {"title": f"Velocity basis: {vb}" if vb else "Delivery timeline",
                 "events": events}
        layout.append({"id": "timeline", "atom": "brevet_timeline", "props": props})
        layout.append({"id": "div-timeline", "atom": "divider"})

    if parsed["backlog"]:
        layout.append({"id": "backlog-heading", "atom": "subheading",
                       "props": {"text": "Backlog"}})
        layout.append({"id": "backlog", "atom": "checklist_interactive",
                       "props": {"items": [("✓ " if b["done"] else "") + b["text"]
                                           for b in parsed["backlog"]]}})
        layout.append({"id": "div-backlog", "atom": "divider"})

    if parsed["risks"]:
        layout.append({"id": "risks-heading", "atom": "subheading",
                       "props": {"text": "Risks"}})
        layout.append({"id": "risks", "atom": "risk_flag",
                       "props": {"title": "Delivery risks",
                                 "risks": parsed["risks"]}})

    payload = {"type": "a2ui_wired_surface", "title": fm["name"],
               "state_primitives": [], "actions": [], "layout": layout}
    if str(fm.get("license", "")).lower() == "private":
        payload["private"] = True
    return payload


def _validate_atoms(payload, lint):
    try:
        with open(SCHEMA) as f:
            known = {b["type"] for b in yaml.safe_load(f)["blocks"]}
    except Exception:
        return
    known |= {"jump_nav", "subheading", "body", "divider"}
    for node in payload["layout"]:
        if node["atom"] not in known:
            lint.w("W01", f"atom '{node['atom']}' not in schema.yaml")


def _report(parsed, lint):
    present = [s for s in ("Phases", "Timeline", "Backlog", "Risks")
               if parsed and (parsed.get(s.lower()) or s == "Phases")]
    n_items = sum(len(ph["items"]) for ph in parsed["phases"]) if parsed else 0
    lines = [f"coverage: {len(present)}/4 sections ({', '.join(present)})",
             f"phases: {len(parsed['phases']) if parsed else 0}, "
             f"items: {n_items}, backlog: {len(parsed['backlog']) if parsed else 0}, "
             f"risks: {len(parsed['risks']) if parsed else 0}"]
    for e in lint.errors:
        lines.append("ERROR " + e)
    for w in lint.warnings:
        lines.append("warn  " + w)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-o", "--out")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    with open(args.file) as f:
        parsed, lint, _ = parse(f.read())

    if lint.errors:
        print(_report(parsed, lint), file=sys.stderr)
        sys.exit(2)

    payload = emit(parsed)
    _validate_atoms(payload, lint)
    if args.report:
        print(_report(parsed, lint), file=sys.stderr)

    out = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out + "\n")
        print(f"wrote {args.out} ({len(out)} chars, "
              f"{len(payload['layout'])} layout nodes)")
    else:
        print(out)


if __name__ == "__main__":
    main()
