"""gen_data_sources.py's guards for a source that spends an upstream credential (upstream_auth)."""
import copy
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("gen_data_sources", ROOT / "scripts" / "gen_data_sources.py")
gds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gds)

DECL = yaml.safe_load((ROOT / "atoms" / "data-sources.yaml").read_text())


def build_with(tmp_path, monkeypatch, mutate):
    d = copy.deepcopy(DECL)
    mutate(d["sources"]["rebrickable_set"])
    p = tmp_path / "ds.yaml"
    p.write_text(yaml.safe_dump(d))
    monkeypatch.setattr(gds, "SRC", p)
    return gds.build()


def test_declared_registry_builds_and_carries_the_secret_name_only():
    reg = gds.build()
    for n in ("rebrickable_set", "rebrickable_set_parts", "rebrickable_colors", "rebrickable_part"):
        assert reg["sources"][n]["upstream_auth"]["secret"] == "REBRICKABLE_API_KEY"
    assert "key " in reg["sources"]["rebrickable_set"]["upstream_auth"]["prefix"]     # the header shape, not a value


@pytest.mark.parametrize("mutate,why", [
    (lambda s: s["upstream_auth"].update(secret="rebrickable_api_key"), "lowercase secret name"),
    (lambda s: s["upstream_auth"].update(secret="AB"), "secret name too short"),
    (lambda s: s["upstream_auth"].update(header="Host"), "header not Authorization or X-*"),
    (lambda s: s["upstream_auth"].update(prefix=5), "prefix not a string"),
    (lambda s: s["upstream_auth"].update(value="hunter2"), "a value must never be declared"),
    (lambda s: s.update(cache_ttl_s=60), "credential source cached under an hour"),
    (lambda s: s["limits"].update(per_ip_per_min=60), "public credential source with a high per-ip limit"),
    (lambda s: s.update(upstream_auth="REBRICKABLE_API_KEY"), "upstream_auth not a mapping"),
])
def test_bad_upstream_auth_is_refused(tmp_path, monkeypatch, mutate, why):
    with pytest.raises(AssertionError):
        build_with(tmp_path, monkeypatch, mutate)


def test_a_source_without_upstream_auth_is_unaffected(tmp_path, monkeypatch):
    def strip(s):
        s.pop("upstream_auth")
        s["cache_ttl_s"] = 10
        s["limits"]["per_ip_per_min"] = 60
    assert "rebrickable_set" in build_with(tmp_path, monkeypatch, strip)["sources"]
