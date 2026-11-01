# Publishing a2uicatalog to PyPI (owner, once)

No token is used anywhere. PyPI trusts this repository's workflow by OIDC ("trusted publishing").

1. On pypi.org, sign in and open Publishing > "Add a new pending publisher" (the project does not exist yet).
   - PyPI project name: `a2uicatalog`
   - Owner: `a2uicatalog`, repository: `a2ui`
   - Workflow file: `pypi-publish.yml`, environment: `pypi`
2. On GitHub, repository Settings > Environments > New environment `pypi` (optionally require your approval).
3. Release: create and push the tag `py-v0.1.0`. The workflow tests, builds, checks the tag against
   `version` in `pyproject.toml`, then publishes.
4. After the first release, set `PYPI_PUBLISHED = True` in `scripts/pypi_flag.py`, run
   `python3 scripts/gen_trust_pages.py` and `python3 scripts/gen_openapi.py`, and commit. Until then the
   site pages do not mention the package, so no link points at a page that does not exist.

Later versions: bump `version` in `pyproject.toml` and `__version__` in `src/a2uicatalog/__init__.py`
(a test keeps them equal), then tag `py-v<version>`.
