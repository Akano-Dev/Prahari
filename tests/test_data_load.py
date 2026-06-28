"""Tests for the dataset loader / unifier."""
from __future__ import annotations

import pandas as pd

from prahari import config
from prahari.data.load import (
    _normalize_label,
    build_dataset,
    clean_text,
)
from prahari.config import DATASET_SPECS


def test_clean_text_collapses_whitespace_and_controls():
    assert clean_text("  hello\t\n  world  ") == "hello world"
    assert clean_text("a\x00b\x07c") == "abc"
    assert clean_text(None) == ""
    assert clean_text(float("nan")) == ""


def test_normalize_label_tokens_and_numeric():
    sms = next(s for s in DATASET_SPECS if s.key == "sms_spam")
    fraud = next(s for s in DATASET_SPECS if s.key == "fraud_email")
    assert _normalize_label("ham", sms) == config.LABEL_LEGIT
    assert _normalize_label("spam", sms) == config.LABEL_SCAM
    # Numeric labels normalise via the spec's value map (1.0 -> "1").
    assert _normalize_label(1.0, fraud) == config.LABEL_SCAM
    assert _normalize_label(0, fraud) == config.LABEL_LEGIT
    assert _normalize_label("???", sms) is None


def test_build_dataset_with_extra_dedups_and_balances(tmp_path):
    extra = pd.DataFrame({
        "text": ["You are under digital arrest", "You are under digital arrest",
                 "Lunch at 1?", "x"],  # one dup, one too-short ("x")
        "label": [config.LABEL_SCAM, config.LABEL_SCAM,
                  config.LABEL_LEGIT, config.LABEL_LEGIT],
        "source": ["t", "t", "t", "t"],
    })
    # Point raw_dir at an empty dir so only `extra` contributes.
    df, summary = build_dataset(raw_dir=tmp_path, extra=extra, write=False)
    assert summary["rows"] == 2  # dup + too-short removed
    assert set(df["label"]) <= set(config.LABELS)
    assert summary["duplicates_removed"] == 2


def test_build_dataset_empty_is_graceful(tmp_path):
    df, summary = build_dataset(raw_dir=tmp_path, write=False)
    assert summary["rows"] == 0
    assert list(df.columns) == ["text", "label", "source"]
