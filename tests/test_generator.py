"""Tests for the synthetic example generator."""
from __future__ import annotations

from prahari import config
from prahari.features.red_flags import rule_score
from prahari.generator import generate


def test_generate_counts_and_schema():
    df = generate(n_scam=50, n_legit=50, seed=7)
    assert list(df.columns) == ["text", "label", "source"]
    assert (df["source"] == "synthetic").all()
    assert (df["label"] == config.LABEL_SCAM).sum() == 50
    assert (df["label"] == config.LABEL_LEGIT).sum() == 50


def test_generate_is_deterministic_per_seed():
    a = generate(n_scam=20, n_legit=20, seed=7)
    b = generate(n_scam=20, n_legit=20, seed=7)
    assert a.equals(b)
    c = generate(n_scam=20, n_legit=20, seed=8)
    assert not a.equals(c)


def test_scam_examples_trigger_red_flags():
    df = generate(n_scam=40, n_legit=0, seed=11)
    scores = df["text"].map(rule_score)
    # Synthetic scam scripts should look unambiguously scammy on average.
    assert scores.mean() > 0.7
    assert (scores > 0.5).mean() > 0.9


def test_legit_examples_are_mostly_quiet():
    df = generate(n_scam=0, n_legit=40, seed=11)
    scores = df["text"].map(rule_score)
    assert scores.mean() < 0.3
