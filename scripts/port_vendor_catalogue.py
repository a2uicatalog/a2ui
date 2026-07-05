#!/usr/bin/env python3
"""port_vendor_catalogue.py — Manifest-driven vendor React→Lit Web Component porter.

Converts MIT-licensed React/TypeScript component libraries into Lit Web
Components + A2UI spec entries. Designed to be reusable across any future
vendor catalogue — add a YAML manifest and run.

Usage:
  python3 scripts/port_vendor_catalogue.py \\
      --manifest scripts/vendor_manifests/extendlabs-ui.yaml \\
      [--component ext-button]   # port one component (default: all)
      [--dry-run]                # print diffs, write nothing
      [--spec-only]              # update spec JSON only, skip .ts output
      [--ts-only]                # write .ts files only, skip spec JSON

Output per component:
  components/{output_dir}/{tag_name}.ts  — Lit Web Component scaffold
  spec/gdm-v0.2.json                     — updated with new spec entry (idempotent)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

# ── Repo root ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = REPO_ROOT / "spec" / "gdm-v0.2.json"

# ── Tailwind animation map ───────────────────────────────────────────────────
# Maps Tailwind animate-* class names → (keyframe_name, keyframe_css, usage_css)

TAILWIND_ANIMATION_MAP: dict[str, tuple[str, str, str]] = {
    "animate-shimmer": (
        "ext-shimmer",
        """\
@keyframes ext-shimmer {
  0%   { background-position: 200% center; }
  100% { background-position: -200% center; }
}""",
        "animation: ext-shimmer 2.4s linear infinite;",
    ),
    "animate-glow": (
        "ext-glow",
        """\
@keyframes ext-glow {
  0%, 100% { box-shadow: 0 0 0 2px rgba(0,242,255,0.3), 0 0 14px rgba(0,242,255,0.2); }
  50%       { box-shadow: 0 0 0 3px rgba(0,242,255,0.7), 0 0 28px rgba(0,242,255,0.45); }
}""",
        "animation: ext-glow 2s ease-in-out infinite;",
    ),
    "animate-perimeterShimmer": (
        "ext-perimeter",
        """\
@keyframes ext-perimeter {
  0%   { background-position: 100%   0%; }
  25%  { background-position: 100% 100%; }
  50%  { background-position:   0% 100%; }
  75%  { background-position:   0%   0%; }
  100% { background-position: 100%   0%; }
}""",
        "animation: ext-perimeter 1.6s linear infinite;",
    ),
    "animate-bounce": (
        "ext-bounce",
        """\
@keyframes ext-bounce {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-5px); }
}""",
        "animation: ext-bounce 1.1s ease-in-out infinite;",
    ),
    "animate-spin": (
        "spin",
        "@keyframes spin { to { transform: rotate(360deg); } }",
        "animation: spin 0.7s linear infinite;",
    ),
}

# ── Type mappings ────────────────────────────────────────────────────────────

TS_TO_LIT: dict[str, str] = {
    "string": "String",
    "boolean": "Boolean",
    "bool": "Boolean",
    "number": "Number",
    "object": "Object",
    "array": "Array",
}

TS_TO_SPEC: dict[str, str] = {
    "string": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "number": "number",
    "object": "object",
    "array": "object",
    "Object": "object",
}

# Props auto-dropped from every component regardless of manifest
AUTO_DROP = {
    "className", "class", "style", "ref", "key",
    "asChild", "slot", "id",
    "aria-label", "aria-describedby", "aria-hidden",
}

# ── YAML loader ──────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    import yaml
    return yaml.safe_load(path.read_text()) or {}


# ── TSX parser ────────────────────────────────────────────────────────────────

def _extract_balanced_block(source: str, keyword: str) -> str | None:
    """Find `keyword {` in source and return the content between the balanced braces."""
    m = re.search(keyword + r'\s*\{', source, re.DOTALL)
    if not m:
        return None
    start = m.end() - 1  # position of opening {
    depth = 0
    for i in range(start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[start + 1:i]
    return None


def _extract_cva_variants(source: str) -> dict[str, list[str]]:
    """Extract variant keys from a cva({variants: {...}}) call."""
    variants: dict[str, list[str]] = {}
    cva_body = _extract_balanced_block(source, r"cva\s*\([^,]+,")
    if cva_body is None:
        return variants
    v_body = _extract_balanced_block(cva_body, r"variants\s*:")
    if v_body is None:
        return variants
    # Each top-level key in variants block is a variant axis
    for key_match in re.finditer(r"(\w+)\s*:\s*\{", v_body):
        key = key_match.group(1)
        block = _extract_balanced_block(v_body[key_match.start():], re.escape(key) + r"\s*:")
        if block is not None:
            values = re.findall(r"(\w+)\s*:", block)
            if values:
                variants[key] = values
    return variants


def _extract_interface_props(source: str, interface_name: str) -> list[dict]:
    """Extract props from a TypeScript interface block."""
    pattern = rf"(?:export\s+)?interface\s+{re.escape(interface_name)}[^{{]*\{{(.*?)\}}"
    m = re.search(pattern, source, re.DOTALL)
    if not m:
        return []

    props = []
    block = m.group(1)
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("*"):
            continue
        pm = re.match(r"(\w+)(\??):\s*([^;]+);?\s*(?://\s*(.*))?", line)
        if not pm:
            continue
        name, optional_mark, type_str, comment = pm.groups()
        type_str = type_str.strip()
        props.append({
            "name": name,
            "required": optional_mark != "?",
            "ts_type": type_str,
            "comment": comment or "",
        })
    return props


def _infer_spec_type(ts_type: str) -> str:
    ts_lower = ts_type.lower()
    if "boolean" in ts_lower: return "boolean"
    if "number" in ts_lower: return "number"
    if "[]" in ts_type or "array" in ts_lower: return "object"
    if ts_lower.startswith("record") or ts_lower == "object": return "object"
    if "string" in ts_lower or "|" in ts_type: return "string"
    return "string"


def _infer_lit_type(ts_type: str) -> str:
    spec = _infer_spec_type(ts_type)
    return TS_TO_LIT.get(spec, "String")


def _is_event_handler(name: str, ts_type: str) -> bool:
    return name.startswith("on") and name[2:3].isupper()


def _is_react_internal(name: str, ts_type: str) -> bool:
    react_internals = {"ReactNode", "ReactElement", "CSSProperties", "RefObject"}
    return any(r in ts_type for r in react_internals)


# ── manual_props → internal prop dicts ───────────────────────────────────────

def _normalise_manual_props(manual_props: list[dict]) -> list[dict]:
    """Convert manifest manual_props entries into the internal prop format."""
    result = []
    for mp in manual_props:
        ts_type = mp.get("type", "string")
        spec_type = _infer_spec_type(ts_type)
        lit_type = TS_TO_LIT.get(spec_type, "String")
        entry: dict = {
            "name": mp["name"],
            "required": mp.get("required", False),
            "ts_type": ts_type,
            "spec_type": spec_type,
            "lit_type": lit_type,
            "comment": mp.get("description", ""),
        }
        if "default" in mp:
            entry["default"] = mp["default"]
        result.append(entry)
    return result


# ── Surface compatibility evaluator ──────────────────────────────────────────

def _evaluate_surface(comp_cfg: dict) -> str:
    """Return 'stage_only' | 'sidepanel' | 'both' per the rule set."""
    override = comp_cfg.get("surface_override")
    if override:
        return override

    animations = comp_cfg.get("tailwind_animations", [])
    if animations:
        return "stage_only"

    source_file = comp_cfg.get("source_file", "")
    try:
        source_path = REPO_ROOT / comp_cfg.get("_vendor_source_dir", "") / source_file
        if source_path.exists():
            src = source_path.read_text()
            if re.search(r"Loader2|Spinner|framer|motion", src):
                return "stage_only"
    except Exception:
        pass

    host = comp_cfg.get("host_element", "div")
    if host == "button":
        return "both"

    return "stage_only"


# ── Component-specific render templates ──────────────────────────────────────

def _generate_render(tag: str, host_el: str, has_action: bool, props: list[dict]) -> str:
    """Return a render() method body tailored to the component type."""
    click_attr = "\n        @click=${this._handleClick}" if has_action else ""
    prop_names = {p["name"] for p in props}

    if tag == "ext-badge":
        return """\
  render() {
    return html`
      <span class="badge badge-${this.variant}">
        ${this.text}
      </span>
    `;
  }"""

    if tag == "ext-alert":
        return """\
  render() {
    return html`
      <div role="alert" class="alert alert-${this.variant}">
        ${this.title ? html`<div class="alert-title">${this.title}</div>` : ''}
        ${this.description ? html`<div class="alert-desc">${this.description}</div>` : ''}
      </div>
    `;
  }"""

    if tag == "ext-card":
        return """\
  render() {
    return html`
      <div class="card">
        ${(this.title || this.description) ? html`
          <div class="card-header">
            ${this.title ? html`<div class="card-title">${this.title}</div>` : ''}
            ${this.description ? html`<div class="card-description">${this.description}</div>` : ''}
          </div>` : ''}
        ${this.content ? html`<div class="card-content">${this.content}</div>` : ''}
        ${this.footer ? html`<div class="card-footer">${this.footer}</div>` : ''}
      </div>
    `;
  }"""

    if tag == "ext-checkbox":
        return """\
  private _onChange(e: Event) {
    this.checked = (e.target as HTMLInputElement).checked;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.checked },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <label class="checkbox-wrapper">
        <input
          type="checkbox"
          .checked=${this.checked}
          ?disabled=${this.disabled}
          name=${this.name || ''}
          value=${this.value || ''}
          @change=${this._onChange}
        />
        ${this.label ? html`<span class="checkbox-label">${this.label}</span>` : ''}
      </label>
    `;
  }"""

    if tag == "ext-input":
        return """\
  private _onCommit(e: KeyboardEvent | FocusEvent) {
    if (e.type === 'keydown' && (e as KeyboardEvent).key !== 'Enter') return;
    this.value = (e.target as HTMLInputElement).value;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.value },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <div class="input-root input-${this.variant}">
        ${this.label ? html`<label class="input-label">${this.label}</label>` : ''}
        <input
          class="input-field"
          type=${this.type || 'text'}
          .value=${this.value}
          placeholder=${this.placeholder || ''}
          ?disabled=${this.disabled}
          ?required=${this.required}
          @keydown=${this._onCommit}
          @blur=${this._onCommit}
        />
        ${this.error ? html`<span class="input-error">${this.error}</span>` : ''}
      </div>
    `;
  }"""

    if tag == "ext-label":
        return """\
  render() {
    return html`
      <label for=${this.for || ''}>${this.text}</label>
    `;
  }"""

    if tag == "ext-switch":
        return """\
  private _onToggle() {
    if (this.disabled) return;
    this.checked = !this.checked;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.checked },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <label class="switch-wrapper">
        <button
          role="switch"
          aria-checked=${this.checked ? 'true' : 'false'}
          class="switch-track ${this.checked ? 'checked' : ''}"
          ?disabled=${this.disabled}
          @click=${this._onToggle}
        >
          <span class="switch-thumb"></span>
        </button>
        ${this.label ? html`<span class="switch-label">${this.label}</span>` : ''}
      </label>
    `;
  }"""

    if tag == "ext-textarea":
        return """\
  private _onCommit(e: KeyboardEvent | FocusEvent) {
    if (e.type === 'keydown') {
      const ke = e as KeyboardEvent;
      if (!(ke.key === 'Enter' && ke.ctrlKey)) return;
    }
    this.value = (e.target as HTMLTextAreaElement).value;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.value },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <div class="textarea-root">
        ${this.label ? html`<label class="textarea-label">${this.label}</label>` : ''}
        <textarea
          class="textarea-field"
          .value=${this.value}
          placeholder=${this.placeholder || ''}
          rows=${this.rows || 3}
          ?disabled=${this.disabled}
          ?required=${this.required}
          maxlength=${this.maxLength || ''}
          @keydown=${this._onCommit}
          @blur=${this._onCommit}
        ></textarea>
      </div>
    `;
  }"""

    if tag == "ext-table":
        return """\
  private get _headers(): string[] {
    try { return JSON.parse(this.headers || '[]'); } catch { return []; }
  }
  private get _rows(): string[][] {
    try { return JSON.parse(this.rows || '[]'); } catch { return []; }
  }

  render() {
    const headers = this._headers;
    const rows = this._rows;
    return html`
      <div class="table-wrapper">
        <table class="table">
          ${this.caption ? html`<caption>${this.caption}</caption>` : ''}
          ${headers.length ? html`
            <thead>
              <tr>${headers.map(h => html`<th>${h}</th>`)}</tr>
            </thead>` : ''}
          <tbody>
            ${rows.map(row => html`
              <tr>${row.map(cell => html`<td>${cell}</td>`)}</tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }"""

    if tag == "ext-tabs":
        return """\
  private get _tabs(): Array<{id: string; label: string; content: string}> {
    try { return JSON.parse(this.tabs || '[]'); } catch { return []; }
  }

  private _selectTab(id: string) {
    this.value = id;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: id },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    const tabs = this._tabs;
    const active = this.value || (tabs[0]?.id ?? '');
    const current = tabs.find(t => t.id === active);
    return html`
      <div class="tabs-root">
        <div class="tabs-list" role="tablist">
          ${tabs.map(t => html`
            <button
              role="tab"
              class="tabs-trigger ${t.id === active ? 'active' : ''}"
              aria-selected=${t.id === active ? 'true' : 'false'}
              @click=${() => this._selectTab(t.id)}
            >${t.label}</button>
          `)}
        </div>
        <div class="tabs-content" role="tabpanel">
          ${current?.content ?? ''}
        </div>
      </div>
    `;
  }"""

    # Generic fallback (button-like or unknown)
    return f"""\
  render() {{
    return html`
      <{host_el}{click_attr}>
        ${{this.text || this.label || ''}}
      </{host_el}>
    `;
  }}"""


# ── Lit TypeScript scaffold generator ────────────────────────────────────────

ACTION_TYPES = """\
type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;"""

HANDLE_CLICK = """\
  private _resolveAction(): Action | null {
    if (this.action) return this.action;
    if (this.targetUrl) return { functionCall: { call: 'openUrl', args: { url: this.targetUrl } } };
    return null;
  }

  private async _handleClick(e: Event) {
    if (this.disabled || this.loading) { e.preventDefault(); return; }
    const action = this._resolveAction();
    if (!action) return;
    try {
      if ('event' in action) {
        this.dispatchEvent(new CustomEvent('a2ui-action', {
          detail: { event: action.event },
          bubbles: true, composed: true,
        }));
        return;
      }
      if ('functionCall' in action) {
        const { call, args } = action.functionCall;
        if (call === 'openUrl') {
          const url = args?.url;
          if (typeof url === 'string') window.open(url, '_blank');
          return;
        }
        if (call === 'navigateTab') {
          this.dispatchEvent(new CustomEvent('a2ui-navigate-tab', {
            detail: { tabId: args?.tabId }, bubbles: true, composed: true,
          }));
          return;
        }
        if (call === 'fireEndpoint') {
          let endpoint = args?.endpoint;
          if (typeof endpoint === 'string') {
            this.loading = true;
            const params = new URLSearchParams(window.location.search);
            const ticket = params.get('ticket');
            if (ticket) {
              try {
                const u = new URL(endpoint, window.location.origin);
                u.searchParams.set('ticket', ticket);
                endpoint = u.pathname + u.search;
              } catch (_) { /* keep original */ }
            }
            await fetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(args?.body ?? {}),
            });
          }
          return;
        }
        console.warn(`[{TAG}] unknown functionCall.call: "$\\{call}"`);
      }
    } catch (err) {
      console.error('[{TAG}] action failed', err);
    } finally {
      this.loading = false;
    }
  }"""

# Tags whose action is inline (not via _handleClick) — render has own event wiring
INLINE_ACTION_TAGS = {"ext-checkbox", "ext-switch", "ext-input", "ext-textarea", "ext-tabs"}


def _generate_ts(
    comp_cfg: dict,
    props: list[dict],
    vendor: dict,
    has_action: bool,
) -> str:
    tag = comp_cfg["tag_name"]
    class_name = comp_cfg["class_name"]
    host_el = comp_cfg.get("host_element", "div")
    animations = comp_cfg.get("tailwind_animations", [])
    description = comp_cfg.get("description", "").strip()
    modifications = comp_cfg.get("modifications", "")

    # Build keyframe CSS
    keyframe_blocks = []
    for anim in animations:
        if anim in TAILWIND_ANIMATION_MAP:
            _, kf_css, _ = TAILWIND_ANIMATION_MAP[anim]
            keyframe_blocks.append(kf_css)

    keyframes_section = ""
    if keyframe_blocks:
        keyframes_section = (
            "\n    /* ── Keyframe animations ── */\n\n    "
            + "\n\n    ".join(keyframe_blocks)
            + "\n"
        )

    # Build @property declarations (skip props whose logic lives in render template)
    prop_lines = []
    # Props handled internally in component-specific renders — no @property needed
    render_internal = set()
    for p in props:
        lit_type = p.get("lit_type", "String")
        name = p["name"]
        default = p.get("default", "")

        if name in render_internal:
            continue

        if lit_type == "Boolean":
            prop_lines.append(f"  @property({{ type: Boolean }}) {name} = false;")
        elif lit_type == "Number":
            default_val = default if default != "" else "0"
            prop_lines.append(f"  @property({{ type: Number }}) {name} = {default_val};")
        elif lit_type == "Object":
            if name == "action":
                prop_lines.append(f"  @property({{ type: Object }})  action: Action | null = null;")
            else:
                prop_lines.append(f"  @property({{ type: Object }})  {name}: any = null;")
        else:
            val = f"'{default}'" if default else "''"
            prop_lines.append(f"  @property({{ type: String }})  {name} = {val};")

    props_block = "\n".join(prop_lines)

    # For button-like tags: use _handleClick protocol; others inline their own event logic
    use_handle_click = has_action and tag not in INLINE_ACTION_TAGS
    if use_handle_click:
        action_types_block = ACTION_TYPES + "\n\n"
        click_block = HANDLE_CLICK.replace("{TAG}", tag) + "\n\n"
    elif has_action:
        action_types_block = ACTION_TYPES + "\n\n"
        click_block = ""
    else:
        action_types_block = ""
        click_block = ""

    render_method = _generate_render(tag, host_el, use_handle_click, props)

    return f"""\
import {{ LitElement, css, html }} from 'lit';
import {{ customElement, property }} from 'lit/decorators.js';

/**
 * {tag} — {description}
 *
 * Original source : {vendor.get('url', '')}
 * License         : {vendor.get('license', 'MIT')} — {vendor.get('copyright', '')}
 * Modifications   : {modifications}
 *
 * Action schema (identical to gdm-button for interoperability):
 *   action: {{ event:        {{ name, context? }} }}        → agent-bound
 *   action: {{ functionCall: {{ call, args? }} }}           → local-only
 *     call values: "openUrl" | "navigateTab" | "fireEndpoint"
 */

{action_types_block}@customElement('{tag}')
export class {class_name} extends LitElement {{
{props_block}

{click_block}  static styles = css`
    :host {{ display: block; }}
{keyframes_section}
    /* TODO: add component styles */
  `;

{render_method}
}}
"""


# ── Spec entry generator ──────────────────────────────────────────────────────

def _generate_spec_entry(
    comp_cfg: dict,
    props: list[dict],
    vendor: dict,
    surface: str,
) -> dict:
    in_prompt = surface != "stage_only"
    description = comp_cfg.get("description", "").strip()

    properties: dict[str, dict] = {}
    for p in props:
        if p["name"] in ("action", "targetUrl"):
            properties[p["name"]] = {
                "type": "object",
                "required": False,
                "description": p.get("comment") or "A2UI action: { functionCall } or { event }.",
            }
        else:
            prop_entry: dict = {
                "type": p.get("spec_type", "string"),
                "required": p.get("required", False),
                "description": p.get("comment") or p["name"],
            }
            if "default" in p:
                prop_entry["default"] = p["default"]
            properties[p["name"]] = prop_entry

    entry: dict[str, Any] = {
        "group": comp_cfg.get("group", "atom"),
        "description": description,
        "strict": True,
        "in_prompt": in_prompt,
        "properties": properties,
        "source": {
            "name": vendor["name"],
            "url": vendor["url"],
            "license": vendor["license"],
            "copyright": vendor["copyright"],
            "modifications": comp_cfg.get("modifications", ""),
        },
    }
    return entry


# ── Catalogue writer ──────────────────────────────────────────────────────────

def _update_spec(tag: str, entry: dict, dry_run: bool) -> None:
    spec = json.loads(SPEC_FILE.read_text())
    components = spec.setdefault("components", {})
    action = "UPDATE" if tag in components else "ADD"
    components[tag] = entry
    out = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        print(f"\n[dry-run] Would {action} '{tag}' in {SPEC_FILE.name}")
    else:
        SPEC_FILE.write_text(out)
        print(f"  spec  [{action}] {tag} → {SPEC_FILE.relative_to(REPO_ROOT)}")


def _write_ts(path: Path, content: str, dry_run: bool) -> None:
    action = "UPDATE" if path.exists() else "CREATE"
    if dry_run:
        print(f"\n[dry-run] Would {action} {path.relative_to(REPO_ROOT)}")
        print(textwrap.indent(content[:600] + ("…" if len(content) > 600 else ""), "  "))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"  ts    [{action}] {path.relative_to(REPO_ROOT)}")


# ── Main ──────────────────────────────────────────────────────────────────────

def _process_component(
    comp_cfg: dict,
    vendor: dict,
    dry_run: bool,
    spec_only: bool,
    ts_only: bool,
) -> None:
    tag = comp_cfg["tag_name"]
    print(f"\nPorting {tag}...")

    source_dir = REPO_ROOT / vendor["source_dir"]
    output_dir = REPO_ROOT / vendor["output_dir"]
    comp_cfg["_vendor_source_dir"] = vendor["source_dir"]

    source_path = source_dir / comp_cfg["source_file"]
    if not source_path.exists():
        print(f"  SKIP  source not found: {source_path.relative_to(REPO_ROOT)}")
        return

    source = source_path.read_text()

    drop = set(comp_cfg.get("drop_props", [])) | AUTO_DROP
    overrides: dict = comp_cfg.get("prop_overrides", {}) or {}
    required_forced: set = set(comp_cfg.get("required_props", []) or [])
    manual_props_raw: list = comp_cfg.get("manual_props") or []

    # ── Prop resolution: manual_props wins over TSX extraction ──────────────
    if manual_props_raw:
        # manual_props are authoritative — skip TSX parsing entirely
        props = _normalise_manual_props(manual_props_raw)
        has_action = any(p["name"] == "action" for p in props)
    else:
        # TSX extraction path
        interface_name = comp_cfg.get("props_interface")
        raw_props = _extract_interface_props(source, interface_name) if interface_name else []

        # CVA variant extraction (merged on top)
        cva_variants = _extract_cva_variants(source)
        cva_prop_names = set(cva_variants.keys())

        existing_names = {p["name"] for p in raw_props}
        for cva_key, values in cva_variants.items():
            if cva_key not in existing_names:
                union_type = " | ".join(f'"{v}"' for v in values)
                raw_props.append({
                    "name": cva_key,
                    "required": False,
                    "ts_type": union_type,
                    "comment": f"One of: {', '.join(values)}",
                })

        has_event_handler = False
        props: list[dict] = []
        has_action = False

        for p in raw_props:
            name = p["name"]
            ts_type = p["ts_type"]

            if name in drop:
                continue
            if _is_react_internal(name, ts_type):
                continue
            if _is_event_handler(name, ts_type):
                has_event_handler = True
                continue

            if name in overrides:
                ov = overrides[name]
                if isinstance(ov, dict):
                    if ov.get("rename"):
                        name = ov["rename"]
                    if ov.get("type"):
                        ts_type = ov["type"]
                    if ov.get("description"):
                        p["comment"] = ov["description"]
                p["name"] = name
                p["ts_type"] = ts_type

            p["spec_type"] = _infer_spec_type(ts_type)
            p["lit_type"] = _infer_lit_type(ts_type)

            if name in cva_prop_names:
                default_match = re.search(
                    rf'defaultVariants.*?{re.escape(name)}\s*:\s*["\'](\w+)["\']',
                    source, re.DOTALL,
                )
                if default_match:
                    p["default"] = default_match.group(1)

            if name in required_forced:
                p["required"] = True

            props.append(p)

        # Inject action + targetUrl for interactive components
        if has_event_handler or comp_cfg.get("host_element") == "button":
            has_action = True
            if not any(p["name"] == "action" for p in props):
                props.append({
                    "name": "action",
                    "required": False,
                    "ts_type": "object",
                    "spec_type": "object",
                    "lit_type": "Object",
                    "comment": "A2UI action: { functionCall: { call, args } } or { event: { name } }.",
                })
            if not any(p["name"] == "targetUrl" for p in props):
                props.append({
                    "name": "targetUrl",
                    "required": False,
                    "ts_type": "string",
                    "spec_type": "string",
                    "lit_type": "String",
                    "comment": "Shorthand for action.functionCall openUrl.",
                })

    # ── Surface evaluation ──────────────────────────────────────────────────
    surface = _evaluate_surface(comp_cfg)
    print(f"  props={len(props)}  surface={surface}  action={has_action}")

    # ── Generate & write .ts ────────────────────────────────────────────────
    if not spec_only:
        ts_content = _generate_ts(comp_cfg, props, vendor, has_action)
        ts_path = output_dir / f"{tag.replace('-', '_')}.ts"
        _write_ts(ts_path, ts_content, dry_run)

    # ── Generate & write spec entry ─────────────────────────────────────────
    if not ts_only:
        spec_entry = _generate_spec_entry(comp_cfg, props, vendor, surface)
        _update_spec(tag, spec_entry, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to vendor manifest YAML")
    parser.add_argument("--component", help="Port only this tag-name (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print diffs, write nothing")
    parser.add_argument("--spec-only", action="store_true", help="Update spec JSON only")
    parser.add_argument("--ts-only", action="store_true", help="Write .ts files only")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = _load_yaml(manifest_path)
    vendor = manifest["vendor"]
    components = manifest.get("components", [])

    if args.component:
        components = [c for c in components if c.get("tag_name") == args.component]
        if not components:
            print(f"Component '{args.component}' not found in manifest.", file=sys.stderr)
            sys.exit(1)

    print(f"Vendor : {vendor['name']} ({vendor['license']})")
    print(f"Source : {vendor['source_dir']}")
    print(f"Output : {vendor['output_dir']}")
    if args.dry_run:
        print("Mode   : dry-run")

    for comp in components:
        _process_component(
            comp_cfg=comp,
            vendor=vendor,
            dry_run=args.dry_run,
            spec_only=args.spec_only,
            ts_only=args.ts_only,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
