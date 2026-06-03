"""Shared test fixtures."""

import os
import pytest


@pytest.fixture
def test_fixture_dir():
    """Path to the synthetic Mockitt fixture directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures", "mockitt_export")
