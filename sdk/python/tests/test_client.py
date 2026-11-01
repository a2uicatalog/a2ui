import json

import pytest

from a2uicatalog import (Client, HTTPError, RateLimitError, UnknownAtomError, ValidationError)


def test_render_posts_blocks_and_returns_html(make_client):
    c, t = make_client({("POST", "/api/render"): [(200, {}, b"<!doctype html><h1>Hi</h1>")]})
    html = c.render([{"type": "heading", "text": "Hi"}], title="T", theme="dark")
    assert html.startswith("<!doctype html>")
    method, path, headers, body = t.calls[0]
    assert (method, path) == ("POST", "/api/render")
    assert body == {"blocks": [{"type": "heading", "text": "Hi"}], "title": "T", "theme": "dark"}
    assert headers["content-type"] == "application/json" and headers["user-agent"].startswith("a2uicatalog-python/")


def test_render_surface_goes_in_the_query_and_is_checked(make_client):
    c, t = make_client({("POST", "/api/render"): [(200, {}, b"<p>")]})
    c.render({"blocks": []}, surface="web")
    assert t.calls[0][1] == "/api/render?surface=web"
    with pytest.raises(ValueError):
        c.render({"blocks": []}, surface="pdf")


def test_render_batch_limits_and_shape(make_client):
    res = {"ok": True, "rendered": 1, "failed": 0, "results": [{"index": 0, "status": 200, "html": "<p>"}]}
    c, t = make_client({("POST", "/api/render/batch"): [(200, {}, res)]})
    assert c.render_batch([[{"type": "heading", "text": "a"}]])["rendered"] == 1
    assert t.calls[0][3] == {"payloads": [{"blocks": [{"type": "heading", "text": "a"}]}]}
    with pytest.raises(ValueError):
        c.render_batch([])
    with pytest.raises(ValueError):
        c.render_batch([{"blocks": []}] * 26)


def test_compose_and_ask(make_client):
    c, t = make_client({("POST", "/api/compose"): [(200, {}, {"blocks": []})],
                        ("POST", "/ask"): [(200, {}, {"results": []})]})
    c.compose("a dashboard", idempotency_key="k1")
    c.ask("countdown timer")
    assert t.calls[0][2]["idempotency-key"] == "k1" and t.calls[0][3] == {"prompt": "a dashboard"}
    assert t.calls[1][3] == {"query": "countdown timer", "mode": "list"}


def test_spec_is_cached(make_client):
    c, t = make_client({("GET", "/spec.json"): [(200, {}, {"atomCount": 2})]})
    assert c.spec()["atomCount"] == 2 and c.spec()["atomCount"] == 2
    assert len(t.calls) == 1


def test_429_retries_once_after_retry_after(make_client):
    slept = []
    c, t = make_client({("POST", "/api/render"): [(429, {"retry-after": "2"}, b"{}"), (200, {}, b"<p>ok")]},
                       sleep=slept.append)
    assert c.render([]) == "<p>ok"
    assert slept == [2.0] and len(t.calls) == 2


def test_429_twice_raises_and_does_not_loop(make_client):
    c, t = make_client({("POST", "/api/render"): [(429, {"retry-after": "1"}, b'{"error":"slow down"}')]})
    with pytest.raises(RateLimitError) as e:
        c.render([])
    assert len(t.calls) == 2 and e.value.retry_after == 1.0


def test_429_with_a_long_wait_raises_without_sleeping(make_client):
    slept = []
    c, t = make_client({("POST", "/api/render"): [(429, {"retry-after": "3600"}, b"{}")]}, sleep=slept.append)
    with pytest.raises(RateLimitError):
        c.render([])
    assert slept == [] and len(t.calls) == 1


def test_http_error_carries_status_and_message(make_client):
    c, _ = make_client({("POST", "/api/render"): [(400, {}, {"error": "bad atom"})]})
    with pytest.raises(HTTPError) as e:
        c.render([])
    assert e.value.status == 400 and "bad atom" in str(e.value)


def test_validate_rejects_an_unknown_atom_by_name(make_client, schema_routes):
    c, _ = make_client(schema_routes)
    with pytest.raises(ValidationError) as e:
        c.validate({"blocks": [{"type": "headng", "text": "x"}]})
    assert "unknown atom type 'headng'" in str(e.value) and "heading" in str(e.value)


def test_validate_missing_extra_and_wrong_type(make_client, schema_routes):
    c, _ = make_client(schema_routes)
    problems = c.check([{"type": "heading"}, {"type": "heading", "text": 3, "bogus": 1}, {"nope": 1}, "x"])
    assert any("missing required field 'text'" in p for p in problems)
    assert any("field 'text' should be string" in p for p in problems)
    assert any("unknown field 'bogus'" in p for p in problems)
    assert any("missing 'type'" in p for p in problems)
    assert any("must be an object" in p for p in problems)
    assert c.check({"blocks": [{"type": "heading", "text": "ok"}]}) == []


def test_schema_fetched_once_for_many_checks(make_client, schema_routes):
    c, t = make_client(schema_routes)
    c.check([{"type": "heading", "text": "a"}]); c.check([{"type": "heading", "text": "b"}])
    assert len(t.calls) == 1


def test_atom_schema_and_unknown(make_client, schema_routes):
    c, _ = make_client(schema_routes)
    assert c.atom_schema("heading")["required"] == ["type", "text"]
    with pytest.raises(UnknownAtomError) as e:
        c.atom_schema("stat_crd")
    assert e.value.suggestions == ["stat_card"]


def test_non_strict_reports_only_unknown_atoms_and_missing_required(make_client, schema_routes):
    c, _ = make_client(schema_routes)
    problems = c.check([{"type": "heading", "text": 3, "bogus": 1}, {"type": "nope"}], strict=False)
    assert problems == ["blocks[1]: unknown atom type 'nope'"]
    c.validate([{"type": "heading", "text": 3, "bogus": 1}], strict=False)


def test_version_matches_pyproject():
    from pathlib import Path
    try:
        import tomllib
    except ImportError:   # Python 3.10
        import tomli as tomllib
    import a2uicatalog
    pp = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert tomllib.loads(pp.read_text())["project"]["version"] == a2uicatalog.__version__
