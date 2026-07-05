"""Shared fixtures for a2ui-catalogue tests."""

import sys
from pathlib import Path
import pytest
import yaml

# Ensure catalogue root is on path
CATALOGUE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALOGUE_ROOT))

SCHEMA_PATH = CATALOGUE_ROOT / "atoms" / "schema.yaml"
SURFACES = ["web", "google-meet-stage", "google-chat", "email", "pdf", "google-apps-script-web", "google-apps-script-side-panel"]


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
