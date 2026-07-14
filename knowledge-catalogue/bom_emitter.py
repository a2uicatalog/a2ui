#!/usr/bin/env python3
"""bom_emitter.py — the generic BOM-driven emitter (runbook-as-data).

Replaces Prompt 3 (the LLM A2UI Transformer) with a DETERMINISTIC stamp:
    approved curriculum.md files  +  BOM schema YAML  →  A2UI v1.0 envelope

The judgment lives in the DECLARED artifacts, not in a prompt:
  - the BOM's atom_type_map decides which atom renders each section kind
  - each kind has ONE authored template component subtree here, stamped over
    the content arrays via the ChildList TEMPLATE variant ({componentId, path})
    with relative-path property bindings — the spec's own one-template-N-rows
    mechanism (decode side shipped 2026-07-10, atoms_v1_decode.gs; the pairing
    rule "never emit what nothing decodes" is satisfied)
  - content is DATA: every section body is extracted into the envelope's
    dataModel; components never embed content

Honesty rules (deterministic means never inventing):
  - `piege` maps to knowledge_check in the BOM, but an MCQ needs invented
    distractors — a judgment call. The emitter DOWNGRADES piège to a warning
    callout and records the downgrade in the envelope's _emitter block.
  - A required_competency with no section still appears (flagged card), the
    same completeness contract Prompt 2 enforces.

Usage:
    python3 bom_emitter.py --schema schemas/national-education/fr/dnb-2026.yaml \\
        --out /tmp/brevet.v1.json  curriculum1.md curriculum2.md ...
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

WEIGHT_ORDER = {"high": 0, "medium": 1, "low": 2}

# ── curriculum.md parser (deterministic; format per knowledge-catalogue/SPEC.md) ──

SECTION_RE = re.compile(r"^## (.+?)\s*\{#([\w-]+)((?:\s+\.[\w-]+)*)\}\s*$")
COMPETENCY_RE = re.compile(r"^<!--\s*competency:\s*([\w-]+)\s*-->\s*$")
GROUP_RE = re.compile(r"^# (?!#)(.+)$")
# Real LLM output (not hand-authored examples) doesn't reliably use the
# **term**: definition bold-colon style — a live 2026-07-14 extraction wrote
# glossary lines as `term` — definition (backticks + em-dash), which the
# original single pattern silently missed entirely: it fell through to the
# "no cards matched" fallback and collapsed 6 real terms into ONE flashcard
# containing the whole raw bullet list as unreadable body text — no error,
# no signal, just a much worse card that would ship unnoticed. Try each
# pattern in turn rather than widening one regex into an unreadable mega-alternation.
GLOSSARY_PATTERNS = [
    re.compile(r"^-\s+\*\*(.+?)\*\*\s*[:—]\s*(.+)$"),   # - **term**: def   |  - **term** — def
    re.compile(r"^-\s+`(.+?)`\s*[:—]\s*(.+)$"),         # - `term` — def   |  - `term`: def
    re.compile(r"^-\s+([^:—`*]+?)\s*[:—]\s*(.+)$"),     # - term: def      |  - term — def (plain)
]
TIMELINE_RE = re.compile(r"^### (.+?)\s*\|\s*(.+)$")
PIEGE_RE = re.compile(r"^>\s*\[!PI[ÈE]GE\]\s*$", re.I)


def match_glossary_line(line):
    for pat in GLOSSARY_PATTERNS:
        m = pat.match(line)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return None


def _strip_frontmatter_fence(text):
    """Real LLM output (not hand-authored examples) sometimes wraps the YAML
    frontmatter in a ```yml / ```yaml fenced code block instead of bare ---
    delimiters — confirmed live 2026-07-14 (@cf/meta/llama-3.3-70b-instruct-fp8-fast).
    That's not a formatting nicety to reject; it's the exact same frontmatter,
    just fenced — normalize the fence to --- before parsing rather than
    crashing on a file that a human would read as obviously well-formed."""
    m = re.match(r"^```ya?ml\s*\n(.*?)\n```\s*\n", text, re.S)
    if m:
        return "---\n" + m.group(1) + "\n---\n" + text[m.end():]
    return text


def parse_frontmatter(text):
    text = _strip_frontmatter_fence(text)
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("curriculum.md missing YAML frontmatter")
    return yaml.safe_load(m.group(1)), text[m.end():]


def parse_curriculum(path):
    front, body = parse_frontmatter(Path(path).read_text())
    groups, cur_group, cur_sect, pending_comp = [], None, None, None

    def close_sect():
        nonlocal cur_sect
        if cur_sect:
            cur_sect["body"] = "\n".join(cur_sect["body"]).strip()
            cur_group["sections"].append(cur_sect)
            cur_sect = None

    def open_group(title):
        nonlocal cur_group
        close_sect()
        cur_group = {"title": title.strip(), "sections": []}
        groups.append(cur_group)

    open_group(front.get("name", "Contenu"))
    first_group_synthetic = True
    for line in body.split("\n"):
        gm = GROUP_RE.match(line)
        if gm:
            if first_group_synthetic and not groups[0]["sections"]:
                groups.pop()
            first_group_synthetic = False
            open_group(gm.group(1))
            continue
        cm = COMPETENCY_RE.match(line)
        if cm:
            pending_comp = cm.group(1)
            continue
        sm = SECTION_RE.match(line)
        if sm:
            close_sect()
            classes = [c[1:] for c in sm.group(3).split()]
            weight = next((c.split("-")[1] for c in classes if c.startswith("weight-")), "medium")
            cur_sect = {"title": sm.group(1).strip(), "kind": sm.group(2),
                        "classes": classes, "weight": weight,
                        "competency": pending_comp, "body": []}
            pending_comp = None
            continue
        if cur_sect is not None:
            cur_sect["body"].append(line)
    close_sect()
    return front, [g for g in groups if g["sections"]]


# ── per-kind content extractors (body markdown → atom-ready data) ───────────────

def _split_pieges(body):
    """Pull [!PIÈGE] blockquote callouts out of a section body."""
    lines, pieges, rest, in_piege, buf = body.split("\n"), [], [], False, []
    for ln in lines:
        if PIEGE_RE.match(ln):
            in_piege, buf = True, []
            continue
        if in_piege:
            if ln.startswith(">"):
                buf.append(ln.lstrip("> ").strip())
                continue
            pieges.append(" ".join(buf).strip())
            in_piege = False
        rest.append(ln)
    if in_piege:
        pieges.append(" ".join(buf).strip())
    return "\n".join(rest).strip(), [p for p in pieges if p]


def _md_table(body):
    rows = []
    for ln in body.split("\n"):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def extract_section(sect):
    """→ (item dict for the kind's data array, [piège texts])."""
    body, pieges = _split_pieges(sect["body"])
    kind, title = sect["kind"], sect["title"]
    item = {"title": title, "weight": sect["weight"], "competency": sect["competency"] or ""}

    if kind in ("concept", "comparison"):
        item["cards"] = [{"front": title, "back": re.sub(r"\n{2,}", "\n", body)}]
    elif kind == "glossary":
        # A markdown TABLE (term | definition | example...) is a real format
        # a model produces for glossary content — confirmed live 2026-07-14
        # in an already-shipped brevet-2026-francais.curriculum.md ("figures
        # de style", 3 columns: term/definition/example). Table rows are a
        # stronger structural signal than bullet lines, so try them first;
        # _md_table already exists for "drill" sections, reused here rather
        # than duplicating table-parsing logic.
        rows = _md_table(body)
        if len(rows) > 1:
            cards = []
            for r in rows[1:]:
                if len(r) < 2:
                    continue
                term = re.sub(r"\*\*(.+?)\*\*", r"\1", r[0]).strip()
                back = " — ".join(c.strip() for c in r[1:] if c.strip())
                cards.append({"front": term, "back": back})
        else:
            matches = [match_glossary_line(ln.strip()) for ln in body.split("\n")]
            cards = [{"front": front, "back": back} for m in matches if m for front, back in [m]]
        item["cards"] = cards or [{"front": title, "back": body}]
    elif kind == "drill":
        rows = _md_table(body)
        data = rows[1:] if len(rows) > 1 else []
        item["questions"] = [{"q": r[0], "a": r[1]} for r in data if len(r) >= 2]
        item["no_calculator"] = "no-calculator" in sect["classes"]
    elif kind == "method":
        steps = [re.sub(r"^\d+[.)]\s*", "", ln.strip())
                 for ln in body.split("\n") if re.match(r"^\d+[.)]\s+", ln.strip())]
        item["items"] = steps or [body]
    elif kind == "key_takeaways":
        item["points"] = [ln.strip()[2:].strip() for ln in body.split("\n")
                          if ln.strip().startswith("- ")] or [body]
    elif kind == "timeline":
        events, cur = [], None
        for ln in body.split("\n"):
            tm = TIMELINE_RE.match(ln.strip())
            if tm:
                cur = {"date": tm.group(1).strip(), "title": tm.group(2).strip(), "desc": ""}
                events.append(cur)
            elif cur and ln.strip():
                cur["desc"] = (cur["desc"] + " " + ln.strip()).strip()
        item["events"] = events
    else:  # unknown kind: honest passthrough as prose
        item["text"] = body
    return item, pieges


# ── the authored template library: ONE subtree per kind ─────────────────────────
# Property bindings are RELATIVE (no leading /) — they resolve per item under
# the ChildList template's Child Scope. THIS is the whole runbook-as-data bet:
# authored once, stamped N times by data.

def template_components(atom_map):
    def atom_for(kind, default):
        return atom_map.get(kind, default)
    return {
        "concept": [
            {"id": "tpl_concept", "component": atom_for("concept", "flashcard_deck"),
             "label_front": "CONCEPT", "accent": "#6366f1",
             "title": {"path": "title"}, "cards": {"path": "cards"}},
        ],
        "glossary": [
            {"id": "tpl_glossary", "component": atom_for("glossary", "flashcard_deck"),
             "label_front": "TERME", "accent": "#0ea5e9",
             "title": {"path": "title"}, "cards": {"path": "cards"}},
        ],
        "drill": [
            # brevet_automatismes renders no title of its own — the authored
            # subtree pairs a heading with the atom (one template, two nodes)
            {"id": "tpl_drill", "component": "Column",
             "children": ["tpl_drill_head", "tpl_drill_atom"]},
            {"id": "tpl_drill_head", "component": "subheading", "text": {"path": "title"}},
            {"id": "tpl_drill_atom", "component": atom_for("drill", "brevet_automatismes"),
             "questions": {"path": "questions"}},
        ],
        "method": [
            {"id": "tpl_method", "component": atom_for("method", "steps"),
             "title": {"path": "title"}, "items": {"path": "items"}},
        ],
        "key_takeaways": [
            {"id": "tpl_takeaways", "component": atom_for("checklist", "key_takeaways"),
             "points": {"path": "points"}},
        ],
        "timeline": [
            {"id": "tpl_timeline", "component": atom_for("timeline", "brevet_timeline"),
             "title": {"path": "title"}, "events": {"path": "events"}},
        ],
        "piege": [
            # deterministic DOWNGRADE from the BOM's knowledge_check (see header)
            {"id": "tpl_piege", "component": "callout", "icon": "⚠️",
             "text": {"path": "text"}},
        ],
        "other": [
            {"id": "tpl_other", "component": "body", "text": {"path": "text"}},
        ],
    }


KIND_TO_ARRAY = {"concept": "concept", "comparison": "concept", "glossary": "glossary",
                 "drill": "drill", "method": "method", "key_takeaways": "key_takeaways",
                 "timeline": "timeline"}


# ── the emitter ──────────────────────────────────────────────────────────────────

def emit(bom_path, curriculum_paths):
    bom = yaml.safe_load(Path(bom_path).read_text())
    atom_map = bom.get("atom_type_map", {})
    order = bom.get("hub_tab_order", [])
    bom_subjects = bom.get("subjects", {})

    parsed = []
    for p in curriculum_paths:
        front, groups = parse_curriculum(p)
        parsed.append((front, groups))
    key = lambda fp: (order.index(fp[0].get("subject")) if fp[0].get("subject") in order
                      else len(order))
    parsed.sort(key=key)

    data_subjects, components, downgrades, uncovered = [], [], 0, []
    tpl_lib = template_components(atom_map)
    used_kinds = set()
    subj_tab_entries = []

    for si, (front, groups) in enumerate(parsed):
        subj_key = front.get("subject", front["id"])
        meta = bom_subjects.get(subj_key, {})
        covered = set()
        slides_data, slide_tab_entries = [], []
        for gi, group in enumerate(groups):
            arrays = {}
            for sect in group["sections"]:
                if sect["competency"]:
                    covered.add(sect["competency"])
                item, pieges = extract_section(sect)
                akey = KIND_TO_ARRAY.get(sect["kind"], "other")
                if akey == "other" and sect["kind"] not in KIND_TO_ARRAY:
                    item.setdefault("text", sect["body"])
                arrays.setdefault(akey, []).append(item)
                for p in pieges:
                    arrays.setdefault("piege", []).append({"text": "**Piège** — " + p})
                    downgrades += 1
            for arr in arrays.values():
                arr.sort(key=lambda it: WEIGHT_ORDER.get(it.get("weight", "medium"), 1))
            slides_data.append({"label": group["title"], **arrays})

            slide_children = []
            for akey in [k for k in tpl_lib if k in arrays]:
                used_kinds.add(akey)
                wrap_id = f"s{si}_g{gi}_{akey}"
                components.append({
                    "id": wrap_id, "component": "Column",
                    "children": {"componentId": tpl_lib[akey][0]["id"],
                                 "path": f"/subjects/{si}/slides/{gi}/{akey}"}})
                slide_children.append(wrap_id)
            slide_col = f"s{si}_g{gi}"
            components.append({"id": slide_col, "component": "Column",
                               "children": slide_children})
            slide_tab_entries.append({"label": group["title"], "child": slide_col})

        # completeness contract: schema competencies with no section, flagged
        missing = [c for c in front.get("required_competencies", [])
                   if c["id"] not in covered]
        if missing:
            uncovered += [c["id"] for c in missing]
            gap_id = f"s{si}_gaps"
            components.append({"id": gap_id, "component": "callout", "icon": "🕳️",
                               "text": {"path": f"/subjects/{si}/gaps"}})
            slide_tab_entries.append({"label": "⚠ Lacunes", "child": gap_id})

        exam = meta.get("exam", {}) or front.get("exam", {}) or {}
        subj_data = {"label": meta.get("label", front.get("name", subj_key)),
                     "slides": slides_data,
                     "gaps": "Compétences du programme sans section: "
                             + ", ".join(c["label"] for c in missing) if missing else ""}
        data_subjects.append(subj_data)

        inner_id = f"subj_{si}_tabs"
        components.append({"id": inner_id, "component": "Tabs", "tabs": slide_tab_entries})
        subj_col = f"subj_{si}"
        head_id = f"subj_{si}_head"
        components.append({"id": head_id, "component": "subheading",
                           "text": {"path": f"/subjects/{si}/label"}})
        components.append({"id": subj_col, "component": "Column",
                           "children": [head_id, inner_id]})
        icon = meta.get("hub_icon", "")
        subj_tab_entries.append({"label": (icon + " " if icon else "") + subj_data["label"],
                                 "child": subj_col})

    components.append({"id": "subjects_tabs", "component": "Tabs", "tabs": subj_tab_entries})
    components.append({"id": "root", "component": "Column", "children": ["subjects_tabs"]})
    # only ship the template subtrees actually referenced
    for akey in sorted(used_kinds):
        components.extend(tpl_lib[akey])

    return {
        "version": "v1.0",
        "createSurface": {
            "surfaceId": bom.get("id", "bom-surface"),
            "catalogId": "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json",
            "surfaceProperties": {"title": bom.get("name", "Knowledge Surface"),
                                  "theme": "dark"},
            "dataModel": {"subjects": data_subjects},
            "components": components,
        },
        "_emitter": {
            "name": "bom_emitter", "bom": str(bom_path),
            "curricula": [str(p) for p in curriculum_paths],
            "piege_downgrades": downgrades,     # knowledge_check needs invented MCQs → callout
            "uncovered_competencies": uncovered,  # never silent
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("curricula", nargs="+")
    args = ap.parse_args()
    envelope = emit(args.schema, args.curricula)
    Path(args.out).write_text(json.dumps(envelope, ensure_ascii=False, indent=1))
    raw = len(json.dumps(envelope))
    e = envelope["_emitter"]
    print(f"wrote {args.out} — {raw} bytes raw, "
          f"{len(envelope['createSurface']['components'])} components, "
          f"{e['piege_downgrades']} piège downgrades, "
          f"{len(e['uncovered_competencies'])} uncovered competencies")
    if raw > 20000:
        print("note: likely exceeds the ?p= ceiling once encoded — graduate "
              "(emit_deployment) or emit per-subject envelopes", file=sys.stderr)


if __name__ == "__main__":
    main()
