"""atoms/agentic-prose.yaml must stay true to the schema it annotates.

The overlay names atoms in prose — both as keys and, crucially, inside
`not_when` clauses that redirect to a different atom. Either can rot silently
when the schema moves: a renamed atom leaves guidance pointing at a vocabulary
that no longer exists, and a model reading it would confidently emit a type the
validator rejects.

Repo-only by design: this file is NOT compiled into public/spec.json. Publishing
untested selection guidance to a2uicatalog.ai is exactly what `stage: preview`
exists to prevent, one level up.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
PROSE_PATH = ROOT / "atoms" / "agentic-prose.yaml"

pytestmark = pytest.mark.skipif(not PROSE_PATH.exists(),
                                reason="agentic-prose.yaml not present")


@pytest.fixture(scope="module")
def prose():
    return yaml.safe_load(PROSE_PATH.read_text())


@pytest.fixture(scope="module")
def schema_types():
    doc = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())
    return {b["type"] for b in doc["blocks"]}


@pytest.fixture(scope="module")
def scoped_types(prose):
    """Every atom in the catalogs the overlay declares it covers."""
    packs = yaml.safe_load((ROOT / "atoms" / "atom-packs.yaml").read_text())
    out = set()
    for cat in prose["scope"]["catalogs"]:
        assert cat in packs, "declared catalog %s is not in atom-packs.yaml" % cat
        out |= set(packs[cat])
    return out


def test_every_annotated_atom_exists(prose, schema_types):
    missing = sorted(set(prose["atoms"]) - schema_types)
    assert not missing, "annotates atoms absent from schema.yaml: %s" % missing


def test_every_annotated_atom_is_in_the_declared_scope(prose, scoped_types):
    """Guidance for an atom outside the resolved catalogs would be advice a
    model can read but never act on."""
    outside = sorted(set(prose["atoms"]) - scoped_types)
    assert not outside, "annotated but outside the declared catalogs: %s" % outside


def test_each_entry_has_both_halves(prose):
    """`not_when` is the half that does the work — an entry without one is a
    description, which the schema already has."""
    for name, entry in prose["atoms"].items():
        assert (entry.get("use_when") or "").strip(), "%s: no use_when" % name
        assert (entry.get("not_when") or "").strip(), "%s: no not_when" % name


def test_not_when_redirects_name_real_atoms(prose, schema_types):
    """The redirect is what turns a vocabulary into a decision procedure. A
    clause pointing at a nonexistent atom sends the model somewhere it cannot
    go — worse than saying nothing, because it reads as authoritative."""
    known = schema_types
    bad = []
    for name, entry in prose["atoms"].items():
        # Atom-shaped tokens inside parentheses are redirects: "(stat_card)".
        for m in re.finditer(r"\(([a-z][a-z0-9_]{3,})\)", entry["not_when"]):
            token = m.group(1)
            # Only judge tokens that look like atom names, not ordinary prose
            # in brackets — an underscore, or an exact schema hit.
            if ("_" in token or token in known) and token not in known:
                bad.append("%s -> %s" % (name, token))
    assert not bad, "not_when points at atoms that do not exist: %s" % bad


def test_redirects_stay_inside_the_scope(prose, scoped_types):
    """A redirect to a real atom the agent cannot resolve is still a dead end."""
    bad = []
    for name, entry in prose["atoms"].items():
        for m in re.finditer(r"\(([a-z][a-z0-9_]{3,})\)", entry["not_when"]):
            token = m.group(1)
            if "_" in token and token not in scoped_types:
                bad.append("%s -> %s" % (name, token))
    assert not bad, "not_when redirects outside the resolved catalogs: %s" % bad


def test_the_restraint_rule_is_stated_once_at_the_top(prose):
    """The preamble outranks every entry. Without it a vocabulary of 25 atoms
    reads as an invitation to use all of them."""
    preamble = prose.get("preamble", "")
    assert "body" in preamble and "sentence" in preamble


def test_the_overlay_is_not_published(prose):
    """Repo-only. If this ever needs to ship, it goes through the same
    per-artifact opt-in as everything else in public/."""
    manifest = yaml.safe_load((ROOT / "project.yaml").read_text())
    published = manifest.get("policy", {}).get("published", []) or []
    assert not any("agentic-prose" in str(rule) for rule in published)
    assert not (ROOT / "public" / "agentic-prose.yaml").exists()
