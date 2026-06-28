"""Shared pytest fixtures.

A session-scoped fixture trains a small model to the default artifact path so
the ``predict`` and API tests have something to load. Training uses the
synthetic generator (fast, deterministic) and the model file is gitignored.
"""
from __future__ import annotations

import pytest

from prahari.models import predict as predict_mod
from prahari.models import train as train_mod


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Ensure a freshly trained model exists at the default path for tests."""
    train_mod.train(test_size=0.25, seed=123)
    predict_mod.load_model.cache_clear()
    yield
    predict_mod.load_model.cache_clear()
