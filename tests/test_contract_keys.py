"""Pure parts of scripts/contract_keys.py (the I75 sweep runner): no network, no Gemini."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import contract_keys as ck  # noqa: E402

ATOMS = ["alpha", "beta", "gamma"]
REL = {"tests/test_alpha_beta.py": ["alpha", "beta"], "tests/test_gamma.py": ["gamma"]}


def test_a_find_that_occurs_once_is_applied(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "r.py").write_text("<div>x</div>\n<p>y</p>\n")
    done, refused, touched = ck.apply([{"atom": "alpha", "file": "r.py", "find": "<div>", "replace": '<div data-cb="tile">'}], {"r.py": 1})
    assert (done, refused, touched) == (1, [], {"r.py"})
    assert (tmp_path / "r.py").read_text() == '<div data-cb="tile">x</div>\n<p>y</p>\n'


def test_a_find_that_occurs_zero_or_two_times_is_refused(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "r.py").write_text("<p>a</p><p>b</p>")
    edits = [{"atom": "alpha", "file": "r.py", "find": "<p>", "replace": "<p data-cb='x'>"},
             {"atom": "alpha", "file": "r.py", "find": "<li>", "replace": "<li data-cb='x'>"},
             {"atom": "alpha", "file": "other.py", "find": "<p>", "replace": ""}]
    done, refused, _ = ck.apply(edits, {"r.py": 1})
    assert done == 0 and len(refused) == 3
    assert "occurs 2 times" in refused[0] and "occurs 0 times" in refused[1] and "not allowed" in refused[2]
    assert (tmp_path / "r.py").read_text() == "<p>a</p><p>b</p>"


def test_a_repeated_find_is_applied_in_the_live_definition_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    text = "def f(b):\n    return '<p>old</p>'\n\ndef f(b):\n    return '<p>live</p>'\n"
    (tmp_path / "r.py").write_text(text)
    live = (text.rindex("def f("), len(text))
    done, refused, _ = ck.apply([{"atom": "alpha", "file": "r.py", "find": "'<p>", "replace": "'<p data-cb=\"tile\">"}], {"r.py": 1},
                                lambda atom, f, s: [live])
    assert done == 1 and not refused
    assert (tmp_path / "r.py").read_text() == "def f(b):\n    return '<p>old</p>'\n\ndef f(b):\n    return '<p data-cb=\"tile\">live</p>'\n"


def test_a_failed_line_naming_an_atom_pins_that_atom():
    out = "FAILED tests/test_contract_sweep.py::test_contract_and_keys[gas-beta] - AssertionError\n"
    assert ck.attribute_failures(out, ATOMS, REL) == {"beta"}


def test_a_cross_atom_check_pins_the_atoms_its_message_names():
    out = "E   AssertionError: twins differ for gamma\nFAILED tests/test_surface_parity.py::test_parity - AssertionError\n"
    assert ck.attribute_failures(out, ATOMS, REL) == {"gamma"}


def test_an_atoms_own_test_file_pins_the_atoms_it_names():
    out = "FAILED tests/test_alpha_beta.py::test_render - AssertionError\n"
    assert ck.attribute_failures(out, ATOMS, REL) == {"alpha", "beta"}


def test_a_collection_error_with_no_failed_line_fails_the_whole_batch():
    out = "E   SyntaxError: invalid syntax\n1 error in 0.1s\n"
    assert ck.attribute_failures(out, ATOMS, REL, returncode=2) == set(ATOMS)
    assert ck.attribute_failures("3 passed in 1s\n", ATOMS, REL, returncode=0) == set()


def test_now_read_updates_the_baseline_for_the_batch_atoms_only(tmp_path):
    base = tmp_path / "unread.json"
    base.write_text(json.dumps({"alpha": ["a", "b"], "beta": ["c"], "zeta": ["d"]}))
    detail = ('E       AssertionError: now read, so delete from tests/schema_fields_unread_baseline.json:\n'
              'E         {\nE          "alpha": [\nE           "a"\nE          ],\nE          "beta": [\nE           "c"\nE          ],\n'
              'E          "zeta": [\nE           "d"\nE          ]\nE         }\nE       assert not {}\n')
    assert ck.accept_now_read(["alpha", "gamma"], detail, str(base))
    assert json.loads(base.read_text()) == {"alpha": ["b"], "beta": ["c"], "zeta": ["d"]}
    assert not ck.accept_now_read(["gamma"], detail, str(base))


def test_a_reply_with_raw_newlines_in_strings_parses():
    reply = '```json\n{"edits": [{"atom": "alpha", "find": "a\nb", "replace": "a\nc"}], "notes": "ok"}\n```'
    ans = ck.parse_reply(reply)
    assert ans["edits"][0]["find"] == "a\nb" and ans["notes"] == "ok"


def test_a_syntax_error_inside_one_atoms_code_fails_that_atom_alone():
    out = ('E     File "/repo/renderers/web_article.py", line 1008\n'
           "E       '<div style=\"display:flex\">%s</div>'\n"
           'E   IndentationError: unexpected indent\n'
           'ERROR tests/test_contract_sweep.py\nERROR tests/test_gas_twins.py\n')
    seen = []

    def locate(f, line):
        seen.append((f, line))
        return "beta" if line == 1008 else None
    assert ck.attribute_failures(out, ATOMS, REL, 2, locate) == {"beta"}
    assert seen == [("/repo/renderers/web_article.py", 1008)]
    assert ck.attribute_failures(out, ATOMS, REL, 2, lambda f, n: None) == set(ATOMS)
