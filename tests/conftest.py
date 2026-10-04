"""Shared fixtures for a2ui-catalogue tests."""

import sys
from pathlib import Path
import pytest
import yaml

# Ensure catalogue root is on path
CATALOGUE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALOGUE_ROOT))

SCHEMA_PATH = CATALOGUE_ROOT / "atoms" / "schema.yaml"
SURFACES = ["web", "google-meet-stage", "google-chat", "email", "pdf", "google-apps-script-web", "google-apps-script-side-panel", "mcp-apps", "google-chat-chromium-render", "claude-code", "android"]


@pytest.fixture(scope="session")
def schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def atoms(schema):
    return {a["type"]: a for a in schema["blocks"]}


@pytest.fixture(scope="session")
def renderer():
    from renderers.web_article import render
    return render


# ─── Area-scoped collection (2026-10-03, Curtis: "they get tested only if related changes are made") ─────────────────────────
# Three slow areas a renderer/catalogue change cannot reach run only when the change touches them: their own source, or their test
# files. "The change" = everything that differs from the merge base with origin/main (commits, staged, unstaged, untracked).
# Always runs everything when: A2UI_FULL_TESTS=1, under CI (CI=true), or git cannot answer. A file named explicitly on the command
# line always runs. Every skip is reported at the end of the run (nothing is dropped silently).
# Known blind spot: brick_build_3d's Python twin lives inside the shared renderers/web_article.py; a brick edit normally touches its
# GAS twin atoms_brick.gs too (that path re-enables the bricks area), but a Python-only brick edit would not.
import os as _os
import subprocess as _sp

_AREAS = {
    "declaration_prealable": {
        "paths": ("declaration_prealable/", "declaration-prealable-api/"),
        "tests": ("test_declaration_prealable_api", "test_dp2_plan_masse", "test_dp5_elevation", "test_dp6_insertion", "test_intake",
                  "test_parcel_lookup"),
    },
    "blender": {
        "paths": ("scripts/brick_models/", "declaration_prealable/render_wall_3d.py", "scripts/test_threejs_view_math"),
        "tests": ("test_render_blender", "test_render_wall_3d", "test_blender_view_math"),
    },
    "bricks": {
        "paths": ("apps-script-surface/gas-wired-renderer/atoms_brick.gs", "renderers/brick_validate.py", "renderers/brick_parts_validate.py",
                  "scripts/brick_models/", "scripts/ldraw/", "scripts/test_brick", "scripts/gen_parts_parity_cases", "spec/brick-parts",
                  "tests/fixtures/bricks/", "public/bricksdemo/", "public/parts/"),
        "tests": ("test_brickgen", "test_brick_gl_geo", "test_brick_parts_builder", "test_brick_parts_stress", "test_brick_parts_validate_js",
                  "test_brick_parts_validate", "test_bricks_demo", "test_brick_validate_js", "test_brick_validate", "test_brick_web_twin",
                  "test_ldraw_colours_full", "test_ldraw_parts", "test_sketch_to_bricks", "test_generic_stud_occupancy", "test_characters",
                  "test_omr_import", "test_part_checks"),
    },
}
_SCOPE_SKIPPED = []


def _scope_changed_files():
    try:
        git = lambda *a: _sp.run(("git", "-C", str(CATALOGUE_ROOT)) + a, capture_output=True, text=True, timeout=20, check=True).stdout
        base = git("merge-base", "HEAD", "origin/main").strip()
        return set(git("diff", "--name-only", base).split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    except Exception:
        return None


def _scope_skips(config):
    if not hasattr(config, "_a2ui_scope"):
        skips, reason = {}, ""
        if _os.environ.get("A2UI_FULL_TESTS") or _os.environ.get("CI"):
            reason = "full run (A2UI_FULL_TESTS or CI set)"
        else:
            changed = _scope_changed_files()
            if changed is None:
                reason = "full run (git could not report changes)"
            else:
                for area, spec in _AREAS.items():
                    own = {"tests/%s.py" % t for t in spec["tests"]}
                    if not any(f.startswith(spec["paths"]) or f in own for f in changed):
                        for f in own:
                            skips[f] = area
        config._a2ui_scope = (skips, reason)
    return config._a2ui_scope[0]


def pytest_ignore_collect(collection_path, config):
    skips = _scope_skips(config)
    if not skips:
        return None
    try:
        rel = collection_path.resolve().relative_to(CATALOGUE_ROOT.resolve()).as_posix()
    except ValueError:
        return None
    if rel not in skips:
        return None
    for a in config.args:  # named explicitly: always run
        if Path(a.split("::")[0]).resolve() == collection_path.resolve():
            return None
    if (skips[rel], rel) not in _SCOPE_SKIPPED:
        _SCOPE_SKIPPED.append((skips[rel], rel))
    return True


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    reason = getattr(config, "_a2ui_scope", ({}, ""))[1]
    if _SCOPE_SKIPPED:
        areas = sorted({a for a, _ in _SCOPE_SKIPPED})
        terminalreporter.write_sep("-", "area-scoped run: skipped %d test files in %s (no related changes vs origin/main); "
                                        "A2UI_FULL_TESTS=1 runs everything" % (len(_SCOPE_SKIPPED), ", ".join(areas)))
    elif reason:
        terminalreporter.write_sep("-", reason)
