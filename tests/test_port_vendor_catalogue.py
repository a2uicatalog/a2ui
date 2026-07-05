"""Tests for scripts/port_vendor_catalogue.py — the manifest-driven React→Lit porter."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

# Ensure catalogue root + scripts on path
CATALOGUE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALOGUE_ROOT / "scripts"))

from port_vendor_catalogue import (
    _evaluate_surface,
    _extract_cva_variants,
    _extract_interface_props,
    _generate_spec_entry,
    _generate_ts,
    _infer_lit_type,
    _infer_spec_type,
    _is_event_handler,
    _is_react_internal,
    _normalise_manual_props,
)

# ── Type inference ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ts_type,expected", [
    ("string", "string"),
    ("boolean", "boolean"),
    ("number", "number"),
    ('"a" | "b"', "string"),
    ("string[]", "object"),         # [] check runs before string check
    ("Record<string, string>", "object"),  # record prefix check
    ("object", "object"),           # exact match
    ("SomeObject", "string"),       # unknown type falls through to string default
])
def test_infer_spec_type(ts_type, expected):
    assert _infer_spec_type(ts_type) == expected


@pytest.mark.parametrize("ts_type,expected", [
    ("string", "String"),
    ("boolean", "Boolean"),
    ("number", "Number"),
    ("object", "Object"),
])
def test_infer_lit_type(ts_type, expected):
    assert _infer_lit_type(ts_type) == expected


# ── Event handler / React internal detection ──────────────────────────────────

def test_is_event_handler_true():
    assert _is_event_handler("onClick", "MouseEventHandler") is True
    assert _is_event_handler("onChange", "(v: string) => void") is True


def test_is_event_handler_false():
    assert _is_event_handler("variant", "string") is False
    assert _is_event_handler("on", "string") is False  # no uppercase 3rd char


def test_is_react_internal():
    assert _is_react_internal("children", "ReactNode") is True
    assert _is_react_internal("style", "CSSProperties") is True
    assert _is_react_internal("variant", "string") is False


# ── CVA variant extraction ─────────────────────────────────────────────────────

CVA_SOURCE = textwrap.dedent("""\
    const badgeVariants = cva("base", {
      variants: {
        variant: {
          default: "bg-primary",
          secondary: "bg-secondary",
          destructive: "bg-red",
          outline: "border",
        },
        size: {
          sm: "text-xs",
          md: "text-sm",
          lg: "text-base",
        },
      },
      defaultVariants: {
        variant: "default",
        size: "md",
      },
    });
""")


def test_extract_cva_variants_keys():
    v = _extract_cva_variants(CVA_SOURCE)
    assert "variant" in v
    assert "size" in v


def test_extract_cva_variant_values():
    v = _extract_cva_variants(CVA_SOURCE)
    assert set(v["variant"]) == {"default", "secondary", "destructive", "outline"}
    assert set(v["size"]) == {"sm", "md", "lg"}


def test_extract_cva_variants_empty_on_no_match():
    assert _extract_cva_variants("export const x = 'hello'") == {}


# ── Interface prop extraction ──────────────────────────────────────────────────

TS_INTERFACE = textwrap.dedent("""\
    export interface InputRootProps extends React.HTMLAttributes<HTMLDivElement> {
      variant?: "default" | "filled" | "flushed";
      error?: string; // validation error message
      disabled?: boolean;
      required?: boolean;
    }
""")


def test_extract_interface_props_names():
    props = _extract_interface_props(TS_INTERFACE, "InputRootProps")
    names = [p["name"] for p in props]
    assert "variant" in names
    assert "error" in names
    assert "disabled" in names
    assert "required" in names


def test_extract_interface_props_optional():
    props = _extract_interface_props(TS_INTERFACE, "InputRootProps")
    by_name = {p["name"]: p for p in props}
    assert by_name["variant"]["required"] is False
    assert by_name["error"]["required"] is False


def test_extract_interface_props_comment():
    props = _extract_interface_props(TS_INTERFACE, "InputRootProps")
    by_name = {p["name"]: p for p in props}
    assert "validation error message" in by_name["error"]["comment"]


def test_extract_interface_props_missing_returns_empty():
    assert _extract_interface_props(TS_INTERFACE, "NonExistentProps") == []


# ── manual_props normalisation ────────────────────────────────────────────────

MANUAL_PROPS = [
    {"name": "text", "type": "string", "required": True, "description": "Badge label"},
    {"name": "variant", "type": "string", "required": False, "default": "default",
     "description": "Visual style"},
    {"name": "checked", "type": "boolean", "required": False, "description": "Is checked"},
    {"name": "rows", "type": "number", "required": False, "description": "Row count"},
    {"name": "action", "type": "object", "required": False, "description": "A2UI action"},
]


def test_normalise_manual_props_count():
    props = _normalise_manual_props(MANUAL_PROPS)
    assert len(props) == 5


def test_normalise_manual_props_types():
    props = _normalise_manual_props(MANUAL_PROPS)
    by_name = {p["name"]: p for p in props}
    assert by_name["text"]["lit_type"] == "String"
    assert by_name["checked"]["lit_type"] == "Boolean"
    assert by_name["rows"]["lit_type"] == "Number"
    assert by_name["action"]["lit_type"] == "Object"


def test_normalise_manual_props_required():
    props = _normalise_manual_props(MANUAL_PROPS)
    by_name = {p["name"]: p for p in props}
    assert by_name["text"]["required"] is True
    assert by_name["variant"]["required"] is False


def test_normalise_manual_props_default():
    props = _normalise_manual_props(MANUAL_PROPS)
    by_name = {p["name"]: p for p in props}
    assert by_name["variant"]["default"] == "default"
    assert "default" not in by_name["text"]


def test_normalise_manual_props_comment():
    props = _normalise_manual_props(MANUAL_PROPS)
    by_name = {p["name"]: p for p in props}
    assert by_name["text"]["comment"] == "Badge label"


# ── Surface evaluator ─────────────────────────────────────────────────────────

def test_surface_override_wins():
    cfg = {"surface_override": "both", "tailwind_animations": ["animate-shimmer"], "host_element": "div"}
    assert _evaluate_surface(cfg) == "both"


def test_surface_animations_implies_stage_only():
    cfg = {"surface_override": None, "tailwind_animations": ["animate-shimmer"], "host_element": "div"}
    assert _evaluate_surface(cfg) == "stage_only"


def test_surface_button_host_implies_both():
    cfg = {"surface_override": None, "tailwind_animations": [], "host_element": "button"}
    assert _evaluate_surface(cfg) == "both"


def test_surface_default_is_stage_only():
    cfg = {"surface_override": None, "tailwind_animations": [], "host_element": "div"}
    assert _evaluate_surface(cfg) == "stage_only"


# ── Spec entry generation ─────────────────────────────────────────────────────

@pytest.fixture
def badge_cfg():
    return {
        "tag_name": "ext-badge",
        "class_name": "ExtBadge",
        "group": "atom",
        "description": "Status badge.",
        "modifications": "children→text",
    }


@pytest.fixture
def badge_props():
    return _normalise_manual_props([
        {"name": "text", "type": "string", "required": True, "description": "Badge label"},
        {"name": "variant", "type": "string", "required": False, "default": "default",
         "description": "Visual style"},
    ])


@pytest.fixture
def vendor():
    return {
        "name": "Extend UI",
        "url": "https://github.com/extendlabs/ui",
        "license": "MIT",
        "copyright": "Copyright (c) 2024 extendui",
    }


def test_spec_entry_structure(badge_cfg, badge_props, vendor):
    entry = _generate_spec_entry(badge_cfg, badge_props, vendor, "both")
    assert entry["group"] == "atom"
    assert entry["in_prompt"] is True
    assert "text" in entry["properties"]
    assert "variant" in entry["properties"]
    assert entry["strict"] is True


def test_spec_entry_stage_only_not_in_prompt(badge_cfg, badge_props, vendor):
    entry = _generate_spec_entry(badge_cfg, badge_props, vendor, "stage_only")
    assert entry["in_prompt"] is False


def test_spec_entry_source_block(badge_cfg, badge_props, vendor):
    entry = _generate_spec_entry(badge_cfg, badge_props, vendor, "both")
    assert entry["source"]["license"] == "MIT"
    assert entry["source"]["name"] == "Extend UI"


def test_spec_entry_prop_default(badge_cfg, badge_props, vendor):
    entry = _generate_spec_entry(badge_cfg, badge_props, vendor, "both")
    assert entry["properties"]["variant"].get("default") == "default"


def test_spec_entry_required(badge_cfg, badge_props, vendor):
    entry = _generate_spec_entry(badge_cfg, badge_props, vendor, "both")
    assert entry["properties"]["text"]["required"] is True
    assert entry["properties"]["variant"]["required"] is False


# ── TS scaffold generation ────────────────────────────────────────────────────

def test_ts_scaffold_contains_custom_element(badge_cfg, badge_props, vendor):
    ts = _generate_ts(badge_cfg, badge_props, vendor, has_action=False)
    assert "@customElement('ext-badge')" in ts


def test_ts_scaffold_contains_class(badge_cfg, badge_props, vendor):
    ts = _generate_ts(badge_cfg, badge_props, vendor, has_action=False)
    assert "export class ExtBadge extends LitElement" in ts


def test_ts_scaffold_contains_property_declarations(badge_cfg, badge_props, vendor):
    ts = _generate_ts(badge_cfg, badge_props, vendor, has_action=False)
    assert "@property({ type: String })" in ts
    assert "text = ''" in ts
    assert "variant = 'default'" in ts


def test_ts_scaffold_action_types_injected_when_has_action(badge_cfg, badge_props, vendor):
    props_with_action = badge_props + _normalise_manual_props([
        {"name": "action", "type": "object", "required": False, "description": "A2UI action"}
    ])
    ts = _generate_ts(badge_cfg, props_with_action, vendor, has_action=True)
    assert "type Action" in ts


def test_ts_scaffold_no_action_types_without_action(badge_cfg, badge_props, vendor):
    ts = _generate_ts(badge_cfg, badge_props, vendor, has_action=False)
    assert "type Action" not in ts


def test_ts_scaffold_attribution_comment(badge_cfg, badge_props, vendor):
    ts = _generate_ts(badge_cfg, badge_props, vendor, has_action=False)
    assert "https://github.com/extendlabs/ui" in ts
    assert "MIT" in ts


# ── End-to-end: real manifest + real source files ────────────────────────────

MANIFEST_PATH = CATALOGUE_ROOT / "scripts" / "vendor_manifests" / "extendlabs-ui.yaml"
SPEC_PATH = CATALOGUE_ROOT / "spec" / "gdm-v0.2.json"


@pytest.mark.skipif(not MANIFEST_PATH.exists(), reason="manifest not present")
def test_manifest_parseable():
    import yaml
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    assert "vendor" in manifest
    assert "components" in manifest
    assert len(manifest["components"]) > 0


@pytest.mark.skipif(not SPEC_PATH.exists(), reason="spec not present")
def test_all_ext_components_in_spec():
    """Every tag_name in the extendlabs manifest must exist in the spec."""
    import yaml
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    spec = json.loads(SPEC_PATH.read_text())
    components = spec.get("components", {})
    for comp in manifest["components"]:
        tag = comp["tag_name"]
        assert tag in components, f"{tag} missing from spec/gdm-v0.2.json"


@pytest.mark.skipif(not SPEC_PATH.exists(), reason="spec not present")
def test_ext_components_have_required_fields():
    """Each ext-* spec entry must have group, description, in_prompt, properties, source."""
    spec = json.loads(SPEC_PATH.read_text())
    for tag, entry in spec["components"].items():
        if not tag.startswith("ext-"):
            continue
        for field in ("group", "description", "in_prompt", "properties", "source"):
            assert field in entry, f"{tag}: missing '{field}'"
        assert entry["properties"], f"{tag}: empty properties"


@pytest.mark.skipif(not SPEC_PATH.exists(), reason="spec not present")
def test_ext_components_source_has_license():
    spec = json.loads(SPEC_PATH.read_text())
    for tag, entry in spec["components"].items():
        if not tag.startswith("ext-"):
            continue
        src = entry.get("source", {})
        assert src.get("license") == "MIT", f"{tag}: expected MIT license in source"
        assert src.get("name"), f"{tag}: missing source.name"


@pytest.mark.skipif(not CATALOGUE_ROOT.joinpath("components/extendlabs").exists(),
                     reason="components/extendlabs not present")
def test_ts_scaffolds_generated():
    """Each ext-* tag_name must have a corresponding .ts scaffold file."""
    import yaml
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    ts_dir = CATALOGUE_ROOT / "components" / "extendlabs"
    for comp in manifest["components"]:
        tag = comp["tag_name"]
        expected = ts_dir / f"{tag.replace('-', '_')}.ts"
        assert expected.exists(), f"Missing scaffold: {expected.relative_to(CATALOGUE_ROOT)}"


@pytest.mark.skipif(not CATALOGUE_ROOT.joinpath("components/extendlabs").exists(),
                     reason="components/extendlabs not present")
def test_ts_scaffolds_contain_custom_element_decorator():
    ts_dir = CATALOGUE_ROOT / "components" / "extendlabs"
    for ts_file in ts_dir.glob("ext_*.ts"):
        content = ts_file.read_text()
        assert "@customElement(" in content, f"{ts_file.name}: missing @customElement"
        assert "extends LitElement" in content, f"{ts_file.name}: missing LitElement"
