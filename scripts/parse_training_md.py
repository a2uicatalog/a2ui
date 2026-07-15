#!/usr/bin/env python3
"""
Deterministic training.md → a2ui_wired_surface payload parser.

Implements spec/training-md-v0.1.md. No LLM anywhere: content comes from
the MD file, machinery (jump_nav, per-step done ValueStores, done_count,
progress_pct) is derived by fixed rules. Atom hints in heading attributes
are validated (W01) but informational in v0.1 — section defaults decide
the emitted atom.

Round-trip fixture pair:
  examples/clasp-deployment.training.md  →  payloads/clasp-runbook.json

Usage:
  python3 scripts/parse_training_md.py <file.md> [-o out.json] [--report]

Exit codes: 0 ok, 2 lint errors (payload not emitted).
"""
import argparse
import json
import os
import re
import string
import sys

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")

REQUIRED_FRONTMATTER = ["id", "domain", "name", "source", "license"]
OPTIONAL_FRONTMATTER = ["subtype", "audience", "est_minutes", "source_url"]
FORBIDDEN_FRONTMATTER = ["render", "layout", "atoms", "theme", "accent"]
STEP_KEYS = ["cmd", "do", "expect", "note", "verify"]
KNOWN_SECTIONS = ["Prerequisites", "Concepts", "Steps", "Checkpoints",
                  "Troubleshooting", "References"]
# Atoms in the wired renderer but not (yet) in atoms/schema.yaml
EXTRA_WIRED_ATOMS = {"jump_nav", "command_step", "sla_timer_display"}

HEADING_ATTR_RE = re.compile(r"\s*\{([^}]*)\}\s*$")
STEP_HEAD_RE = re.compile(r"^(\d+)\.\s+(.*)$")
NUMBERED_PHASE_RE = re.compile(r"^\d+\s+·")
STEP_KEY_RE = re.compile(r"^([a-z_]+):\s?(.*)$")
INFO_LABEL_RE = re.compile(r"^\*\*(.+)\*\*\s*$")


def _known_atom_types():
    try:
        with open(SCHEMA) as f:
            blocks = yaml.safe_load(f)["blocks"]
        return {b["type"] for b in blocks} | EXTRA_WIRED_ATOMS
    except Exception:
        return EXTRA_WIRED_ATOMS


def _parse_attrs(heading):
    """Strip and parse a trailing {#hint .weight-x nav="..."} block."""
    attrs = {"hint": None, "weight": None, "nav": None}
    m = HEADING_ATTR_RE.search(heading)
    if not m:
        return heading.strip(), attrs
    body = m.group(1)
    title = heading[: m.start()].strip()
    for tok in re.findall(r'nav="[^"]*"|\S+', body):
        if tok.startswith("#"):
            attrs["hint"] = tok[1:]
        elif tok.startswith(".weight-"):
            attrs["weight"] = tok[len(".weight-"):]
        elif tok.startswith('nav="') and tok.endswith('"'):
            attrs["nav"] = tok[5:-1]
    return title, attrs


class Lint:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, msg):
        self.errors.append(f"{code}: {msg}")

    def warn(self, code, msg):
        self.warnings.append(f"{code}: {msg}")


def parse(text):
    """Parse training.md text → (payload_or_None, report dict)."""
    lint = Lint()
    known_atoms = _known_atom_types()

    # Strip a wrapping code fence (the spec asks Gemini to fence its output
    # so it copies losslessly from chat UIs)
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped[stripped.index("\n") + 1:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
        text = stripped.strip() + "\n"

    # Normalize asterisk bullets — both are legal markdown; the section
    # parsers match "- " only
    text = re.sub(r"^(\s*)\* ", r"\1- ", text, flags=re.MULTILINE)

    # --- frontmatter -----------------------------------------------------
    fm_match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        # A real model can drop the closing --- delimiter entirely (confirmed
        # live 2026-07-15, @cf/meta/llama-3.3-70b-instruct-fp8-fast: five
        # clean frontmatter lines, then straight into "# Steps" with no
        # closing ---). Tolerate it ONLY when the content between the
        # opening --- and the first top-level heading parses as clean,
        # non-empty YAML — if it doesn't, fall through to the strict error
        # below rather than silently swallowing unrelated prose into
        # "frontmatter".
        loose = re.match(r"\A---\n(.*?)\n(?=# [^#\n])", text, re.DOTALL)
        if loose:
            try:
                candidate = yaml.safe_load(loose.group(1))
                if isinstance(candidate, dict) and candidate:
                    fm_match = loose
            except yaml.YAMLError:
                pass
    if not fm_match:
        lint.error("E01", "missing or malformed frontmatter (--- block). "
                   "If this was copied from Gemini's rendered reply, use the "
                   "copy button / raw view — rendered copies collapse the "
                   "frontmatter into one line")
        return None, _report(lint, {}, [])
    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as e:
        lint.error("E01", f"frontmatter is not valid YAML: {e}")
        return None, _report(lint, {}, [])
    for key in REQUIRED_FRONTMATTER:
        if not fm.get(key):
            lint.error("E02", f"missing required frontmatter key '{key}'")
    if fm.get("domain") and fm["domain"] != "training":
        lint.error("E03", f"domain is '{fm['domain']}', expected 'training'")
    for key in fm:
        if key in FORBIDDEN_FRONTMATTER:
            lint.error("E09", f"forbidden frontmatter key '{key}' — presentation lives in the runbook")
        elif key not in REQUIRED_FRONTMATTER + OPTIONAL_FRONTMATTER:
            lint.error("E09", f"unknown frontmatter key '{key}'")
    if str(fm.get("license", "")).startswith("Unknown"):
        lint.warn("W04", "license is unverified — confirm before publishing")

    body = text[fm_match.end():]
    lines = body.split("\n")

    # --- split into intro + top-level sections ---------------------------
    intro_lines = []
    sections = []  # (title, attrs, [lines])
    current = None
    for line in lines:
        if line.startswith("# ") and not line.startswith("##"):
            title, attrs = _parse_attrs(line[2:])
            current = (title, attrs, [])
            sections.append(current)
        elif current is None:
            intro_lines.append(line)
        else:
            current[2].append(line)

    # A model naturally wants to label the intro blurb its own heading
    # ("# Introduction") even though the spec asks for unlabeled prose
    # before the first real section — confirmed live 2026-07-15
    # (@cf/meta/llama-3.3-70b-instruct-fp8-fast). Fold it into the intro
    # slot rather than rejecting it as an unknown top-level section (E12).
    # This is the one alias tolerated, not a general "any heading before
    # Steps is fine" rule — a genuinely wrong section name must still fail
    # E12, so only this exact, predictable heading name is special-cased.
    if sections and sections[0][0] == "Introduction":
        intro_lines = intro_lines + sections[0][2]
        sections = sections[1:]

    intro = " ".join(l.strip() for l in intro_lines if l.strip())

    section_names = [s[0] for s in sections]
    for name, attrs, _ in sections:
        if name not in KNOWN_SECTIONS:
            lint.error("E12", f"unknown top-level section '# {name}'")
        if attrs["hint"] and attrs["hint"] not in known_atoms:
            lint.warn("W01", f"unknown atom hint '#{attrs['hint']}' on '# {name}' — default atom used")
    if "Steps" not in section_names:
        lint.error("E04", "no '# Steps' section")

    # --- parse each section ----------------------------------------------
    parsed = {}
    steps_flow = []
    step_count = 0
    for name, attrs, sec_lines in sections:
        if name == "Steps":
            steps_flow, step_count = _parse_steps(sec_lines, lint, known_atoms)
        elif name == "Prerequisites":
            parsed[name] = _parse_bullets(sec_lines)
        elif name == "Concepts":
            parsed[name] = _parse_term_bullets(sec_lines, lint)
        elif name == "Checkpoints":
            parsed[name] = _parse_qa(sec_lines, lint)
        elif name == "Troubleshooting":
            parsed[name] = _parse_sep_bullets(sec_lines, lint, "Troubleshooting")
        elif name == "References":
            parsed[name] = _parse_references(sec_lines)

    if "Steps" in section_names and step_count == 0:
        lint.error("E04", "'# Steps' contains zero steps")

    report = _report(lint, parsed, section_names, step_count)
    if lint.errors:
        return None, report

    payload = _emit(fm, intro, section_names, parsed, steps_flow, step_count)
    return payload, report


# --- section parsers ------------------------------------------------------

def _parse_bullets(sec_lines):
    return [l[2:].strip() for l in sec_lines if l.startswith("- ")]


# Real model output uses several separators/bolding conventions the spec
# doesn't ask for — confirmed live 2026-07-15 (@cf/meta/llama-3.3-70b-
# instruct-fp8-fast) on a real translated blog article: Concepts entries
# used "**term**: definition" (colon, not the spec's em-dash), and
# Troubleshooting entries used "**symptom**: fix" (bold + colon, not the
# spec's plain "symptom :: fix"). Both were silently rejected (E08) despite
# being unambiguous key/definition pairs a human would read as correct.
# Accept " :: ", " — ", or a bare ":" as the separator, and accept the key
# with or without ** bold, in EITHER direction of what the spec nominally
# asks for each section — still requires ONE of these separators to be
# present, so a genuinely malformed bullet with no separator at all still
# raises E08.
_KEY_DESC_RE = re.compile(r"^(?:\*\*(.+?)\*\*|(.+?))\s*(?:::|—|:)\s*(.+)$")


def _split_key_desc(line):
    m = _KEY_DESC_RE.match(line)
    if not m:
        return None
    key = m.group(1) if m.group(1) is not None else m.group(2)
    return key.strip(), m.group(3).strip()


def _parse_term_bullets(sec_lines, lint):
    items = []
    for l in sec_lines:
        if not l.startswith("- "):
            continue
        m = _split_key_desc(l[2:].strip())
        if m:
            items.append({"key": m[0], "description": m[1]})
        else:
            lint.error("E08", f"Concepts entry not in '**term** — definition' form: {l[:60]}")
    return items


def _parse_sep_bullets(sec_lines, lint, section):
    items = []
    for l in sec_lines:
        if not l.startswith("- "):
            continue
        m = _split_key_desc(l[2:].strip())
        if not m:
            lint.error("E08", f"{section} entry without ' :: ' separator: {l[:60]}")
            continue
        items.append({"key": m[0], "description": m[1]})
    return items


def _parse_qa(sec_lines, lint):
    pairs, q = [], None
    for l in sec_lines:
        s = l.strip()
        if s.startswith("Q:"):
            if q is not None:
                lint.error("E10", f"Checkpoints 'Q:' without matching 'A:': {q[:50]}")
            q = s[2:].strip()
        elif s.startswith("A:"):
            if q is None:
                lint.error("E10", f"Checkpoints 'A:' without preceding 'Q:': {s[:50]}")
            else:
                pairs.append({"q": q, "a": s[2:].strip()})
                q = None
    if q is not None:
        lint.error("E10", f"Checkpoints 'Q:' without matching 'A:': {q[:50]}")
    return pairs


def _parse_references(sec_lines):
    items = []
    for l in sec_lines:
        if not l.startswith("- "):
            continue
        entry = l[2:].strip()
        if " — " in entry:
            label, _, url = entry.rpartition(" — ")
            items.append({"title": label.strip(), "url": url.strip()})
        else:
            items.append({"title": entry, "url": entry})
    return items


# --- steps parser ---------------------------------------------------------

def _parse_steps(sec_lines, lint, known_atoms):
    """Return (flow, step_count). flow is a list of phase dicts:
    {title, nav, numbered, elements:[...]}; flat shape produces a single
    implicit phase with title None."""
    h2 = [l for l in sec_lines if l.startswith("## ") and not l.startswith("###")]
    h2_titles = [_parse_attrs(l[3:])[0] for l in h2]
    h2_steppy = [bool(STEP_HEAD_RE.match(t)) for t in h2_titles]
    has_h3 = any(l.startswith("### ") for l in sec_lines)

    if h2 and any(h2_steppy) and (has_h3 or not all(h2_steppy)):
        lint.error("E11", "flat and phased shapes mixed inside '# Steps'")
        return [], 0
    flat = bool(h2) and all(h2_steppy) and not has_h3

    phases = []
    if flat:
        phases.append({"title": None, "nav": None, "numbered": False, "lines": []})
    step_level = "## " if flat else "### "

    current = phases[0] if flat else None
    for line in sec_lines:
        if not flat and line.startswith("## ") and not line.startswith("###"):
            title, attrs = _parse_attrs(line[3:])
            current = {"title": title, "nav": attrs["nav"],
                       "numbered": bool(NUMBERED_PHASE_RE.match(title)), "lines": []}
            phases.append(current)
            continue
        if current is None:
            if line.strip():
                lint.error("E11", f"content before first phase heading in '# Steps': {line[:50]}")
            continue
        current["lines"].append(line)

    step_count = 0
    for phase in phases:
        phase["elements"] = _parse_phase_elements(phase["lines"], step_level, lint, known_atoms, phase)
        del phase["lines"]
        step_count += sum(1 for e in phase["elements"] if e["kind"] == "step")
    return phases, step_count


def _parse_phase_elements(p_lines, step_level, lint, known_atoms, phase):
    elements = []
    i = 0
    expected_n = 1
    while i < len(p_lines):
        line = p_lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith(step_level):
            title, attrs = _parse_attrs(line[len(step_level):])
            m = STEP_HEAD_RE.match(title)
            if not m:
                lint.error("E06", f"step heading not '<n>. <title>': {title[:60]}")
                i += 1
                continue
            if int(m.group(1)) != expected_n:
                lint.error("E06", f"step numbering not sequential: got {m.group(1)}, expected {expected_n} ({title[:50]})")
            expected_n += 1
            if attrs["hint"] and attrs["hint"] not in known_atoms:
                lint.warn("W01", f"unknown atom hint '#{attrs['hint']}' on step '{m.group(2)[:40]}'")
            step = {"kind": "step", "title": m.group(2)}
            i += 1
            while i < len(p_lines):
                l = p_lines[i]
                if not l.strip():
                    break
                km = STEP_KEY_RE.match(l)
                if not km:
                    break
                key, value = km.group(1), km.group(2)
                if key not in STEP_KEYS:
                    lint.error("E07", f"unknown key '{key}:' in step '{step['title'][:40]}'")
                else:
                    step[key] = value
                i += 1
            has_cmd, has_do = "cmd" in step, "do" in step
            if has_cmd == has_do:
                lint.error("E05", f"step '{step['title'][:40]}' must have exactly one of cmd/do")
            if "verify" not in step:
                lint.warn("W03", f"step '{step['title'][:40]}' has no verify — done-checkbox is self-report")
            elements.append(step)
            continue
        if line.startswith("> "):
            quote = []
            while i < len(p_lines) and p_lines[i].startswith(">"):
                quote.append(p_lines[i].lstrip(">").strip())
                i += 1
            elements.append({"kind": "callout", "text": " ".join(q for q in quote if q)})
            continue
        lm = INFO_LABEL_RE.match(line.strip())
        if lm:
            items = []
            i += 1
            while i < len(p_lines) and p_lines[i].startswith("- "):
                entry = p_lines[i][2:]
                m = _split_key_desc(entry.strip())
                if not m:
                    lint.error("E08", f"info-block entry without ' :: ' separator: {entry[:60]}")
                else:
                    items.append({"key": m[0], "description": m[1]})
                i += 1
            elements.append({"kind": "info", "title": lm.group(1), "items": items})
            continue
        # prose paragraph → body atom
        para = []
        while i < len(p_lines) and p_lines[i].strip() and not p_lines[i].startswith(("#", ">", "- ", "**")):
            para.append(p_lines[i].strip())
            i += 1
        if para:
            elements.append({"kind": "body", "text": " ".join(para)})
        else:
            i += 1  # defensive: unparseable line, skip
    return elements


# --- payload emission -----------------------------------------------------

def _letters():
    for c in string.ascii_lowercase:
        yield c
    for c1 in string.ascii_lowercase:
        for c2 in string.ascii_lowercase:
            yield c1 + c2


def _emit(fm, intro, section_names, parsed, phases, step_count):
    layout = []
    state = []
    step_idx = 0
    div_idx = 0
    blk = 0

    def bid(prefix):
        nonlocal blk
        blk += 1
        return f"{prefix}-{blk}"

    layout.append({"id": "title-heading", "atom": "subheading",
                   "props": {"text": fm["name"]}})

    nav_links = []
    phase_heading_ids = {}
    for p_i, phase in enumerate(phases):
        if phase["title"] is not None:
            phase_heading_ids[p_i] = f"phase-{p_i}-heading"
            if phase["numbered"]:
                nav_links.append({"label": phase["nav"] or phase["title"],
                                  "target": phase_heading_ids[p_i]})
    if not phases or (len(phases) == 1 and phases[0]["title"] is None):
        # flat shape: nav from step headings
        pass
    if nav_links:
        layout.append({"id": "nav", "atom": "jump_nav", "props": {"links": nav_links}})
    if intro:
        layout.append({"id": "intro", "atom": "body", "props": {"text": intro}})

    def emit_optional(name):
        if name not in parsed:
            return
        data = parsed[name]
        if not data:
            return
        if name == "Prerequisites":
            layout.append({"id": bid("prereq"), "atom": "prerequisite_checklist",
                           "props": {"title": "Prerequisites", "items": data}})
        elif name == "Concepts":
            layout.append({"id": bid("concepts"), "atom": "key_value",
                           "props": {"title": "Concepts", "items": data}})
        elif name == "Checkpoints":
            for pair in data:
                layout.append({"id": bid("check"), "atom": "accordion_item",
                               "props": {"header": pair["q"], "content": pair["a"]}})
        elif name == "Troubleshooting":
            for item in data:
                layout.append({"id": bid("trouble"), "atom": "accordion_item",
                               "props": {"header": item["key"], "content": item["description"]}})
        elif name == "References":
            layout.append({"id": bid("refs"), "atom": "resources_list",
                           "props": {"items": data}})

    # sections before Steps, in file order
    steps_pos = section_names.index("Steps") if "Steps" in section_names else len(section_names)
    for name in section_names[:steps_pos]:
        emit_optional(name)

    for p_i, phase in enumerate(phases):
        if phase["title"] is not None:
            layout.append({"id": f"div{div_idx}", "atom": "divider"})
            div_idx += 1
            layout.append({"id": phase_heading_ids[p_i], "atom": "subheading",
                           "props": {"text": phase["title"]}})
        for el in phase["elements"]:
            if el["kind"] == "step":
                store_id = f"s_{step_idx + 1}"
                state.append({"id": store_id, "primitive": "ValueStore",
                              "props": {"defaultValue": False, "persist": True}})
                props = {"label": el["title"],
                         "command": el.get("cmd", el.get("do", ""))}
                hint_parts = []
                if el.get("note"):
                    hint_parts.append(el["note"])
                if el.get("expect"):
                    hint_parts.append(f"Expect: {el['expect']}")
                if el.get("verify"):
                    hint_parts.append(f"Verify: {el['verify']}")
                if hint_parts:
                    props["hint"] = " — ".join(hint_parts)
                layout.append({"id": f"cmd-{step_idx + 1}", "atom": "command_step",
                               "props": props,
                               "wire": {"done": f"#{store_id}.value",
                                        "setDone": f"#{store_id}.setValue"}})
                step_idx += 1
            elif el["kind"] == "callout":
                layout.append({"id": bid("callout"), "atom": "callout",
                               "props": {"type": "warning", "text": el["text"]}})
            elif el["kind"] == "info":
                layout.append({"id": bid("info"), "atom": "key_value",
                               "props": {"title": el["title"], "items": el["items"]}})
            elif el["kind"] == "body":
                layout.append({"id": bid("body"), "atom": "body",
                               "props": {"text": el["text"]}})

    for name in section_names[steps_pos + 1:]:
        emit_optional(name)

    src = str(fm.get("source", "")).strip()
    lic = str(fm.get("license", "")).strip()
    src_url = str(fm.get("source_url", "")).strip()
    attribution = f"Source: {src}"
    if src_url:
        attribution = f"Source: [{src}]({src_url})"
    if lic:
        attribution += f" · License: {lic}"
    layout.append({"id": "attribution", "atom": "body",
                   "props": {"text": f"*{attribution}*"}})

    if step_count:
        letters = _letters()
        inputs = {}
        expr_terms = []
        for i in range(step_count):
            letter = next(letters)
            inputs[letter] = f"#s_{i + 1}.value"
            expr_terms.append(letter)
        state.append({"id": "done_count", "primitive": "Computed",
                      "props": {"expr": "+".join(expr_terms), "inputs": inputs}})
        state.append({"id": "progress_pct", "primitive": "Computed",
                      "props": {"expr": f"n/{step_count}*100",
                                "inputs": {"n": "#done_count.value"}}})

    return {"type": "a2ui_wired_surface", "title": fm["name"],
            "state_primitives": state, "actions": [], "layout": layout}


def _report(lint, parsed, section_names, step_count=0):
    optional = [s for s in KNOWN_SECTIONS if s != "Steps"]
    absent = [s for s in optional if s not in section_names]
    for s in absent:
        lint.warn("W02", f"optional section absent: {s}")
    return {
        "errors": lint.errors,
        "warnings": lint.warnings,
        "sections_present": [s for s in section_names if s in KNOWN_SECTIONS],
        "sections_absent": absent,
        "step_count": step_count,
        "coverage": f"{len([s for s in section_names if s in KNOWN_SECTIONS])}/{len(KNOWN_SECTIONS)} sections",
    }


def main():
    ap = argparse.ArgumentParser(description="training.md → wired payload")
    ap.add_argument("file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    with open(args.file) as f:
        payload, report = parse(f.read())

    if args.report or report["errors"]:
        for e in report["errors"]:
            print(f"❌ {e}", file=sys.stderr)
        for w in report["warnings"]:
            print(f"⚠️  {w}", file=sys.stderr)
        print(f"coverage: {report['coverage']}; steps: {report['step_count']}", file=sys.stderr)
    if report["errors"]:
        sys.exit(2)

    out = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"✅ {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
