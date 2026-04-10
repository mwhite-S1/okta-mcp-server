# The Okta software accompanied by this notice is provided pursuant to the following terms:
# Copyright © 2026-Present, Okta, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""Pytest fixtures for live integration tests.

These fixtures provide session-scoped authentication, shared test data, and
managed objects (with cleanup) so the test functions in test_governance_live.py
can run under pytest without requiring the standalone script's main() function.
"""

from __future__ import annotations

import os
import sys
import time
from urllib.parse import urlencode

import pytest

# Ensure the live test directory is on sys.path so we can import helpers.
_live_dir = os.path.dirname(__file__)
if _live_dir not in sys.path:
    sys.path.insert(0, _live_dir)

# Load .env before importing the test module (which reads os.environ at import time).
_env_path = os.path.join(_live_dir, "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from test_governance_live import (  # noqa: E402
    _get_token,
    _fetch_principal_id,
    _fetch_resource_orns,
    _create_label_for_test,
    _scan_catalog,
    call,
    _items,
    cleanup_label,
)


# ---------------------------------------------------------------------------
# Session-scoped auth / shared data
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def token():
    """Obtain a single access token for the entire test session."""
    return _get_token()


@pytest.fixture(scope="session")
def principal_id(token):
    """Fetch a real Okta user ID to use as a principal in governance calls."""
    return _fetch_principal_id(token)


@pytest.fixture(scope="session")
def resource_orns(token):
    """Fetch real resource ORNs from the governance catalog."""
    return _fetch_resource_orns(token)


# ---------------------------------------------------------------------------
# Managed label (created once, cleaned up after the session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def created_label(token):
    """Create a governance label, yield it to tests, then delete it."""
    created = _create_label_for_test(token)
    label_id = created.get("_label_id", "")
    print(f"\n  [fixture] created_label: {label_id}")
    yield created
    if label_id:
        cleanup_label(label_id, token)


# ---------------------------------------------------------------------------
# Catalog discovery (entry_id + resource_id derived once per session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def catalog_info(token):
    """Scan catalog entries to find a usable entry_id and an app resource_id
    that has request sequences configured.  Returns (entry_id, resource_id).
    """
    entry_id, resource_id = _scan_catalog(token)
    print(f"\n  [fixture] catalog_info: entry_id={entry_id!r} resource_id={resource_id!r}")
    return entry_id, resource_id


@pytest.fixture(scope="session")
def entry_id(catalog_info):
    return catalog_info[0]


@pytest.fixture(scope="session")
def resource_id(catalog_info):
    return catalog_info[1]
