"""Numeric / structural features for the classical ML model.

These complement the TF-IDF bag-of-words with hand-crafted signals that the
bag-of-words misses: how many red-flag categories fired, the urgency of the
text, presence of money/links/phone numbers, casing and punctuation intensity.

The core export is :class:`NumericFeatureExtractor`, a tiny scikit-learn
compatible transformer so it can drop straight into a ``FeatureUnion`` /
``Pipeline`` and be persisted with :mod:`joblib` alongside the vectorizer.
"""
from __future__ import annotations

import re

import numpy as np

from prahari.features.red_flags import RULES, scan

# Pre-compiled structural patterns (independent of the red-flag rules).
_RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_RE_MONEY = re.compile(r"(?:₹|\b(?:rs|inr)\b|\brupees?\b|\blakhs?\b|\bcrores?\b)", re.IGNORECASE)
_RE_PHONE = re.compile(r"\b(?:\+?91[\-\s]?)?\d{10}\b|\b1930\b")
_RE_DIGIT = re.compile(r"\d")
_RE_UPPER_WORD = re.compile(r"\b[A-Z]{3,}\b")

# Stable feature order. One column per red-flag category (did it fire? 0/1)
# followed by the structural features below.
_FLAG_FEATURES = [f"flag_{r.id}" for r in RULES]
_STRUCT_FEATURES = [
    "n_flags",            # how many distinct red-flag categories fired
    "flag_weight",        # summed severity of fired flags
    "char_len",           # length in characters (log1p-scaled)
    "word_len",           # length in words (log1p-scaled)
    "uppercase_ratio",    # fraction of letters that are uppercase
    "digit_ratio",        # fraction of chars that are digits
    "n_exclaim",          # number of '!' (capped)
    "n_upper_words",      # ALL-CAPS words like "URGENT" (capped)
    "has_url",            # contains a link
    "n_money",            # currency mentions (capped)
    "has_phone",          # contains a 10-digit / helpline number
]
FEATURE_NAMES: list[str] = _FLAG_FEATURES + _STRUCT_FEATURES


def _features_for(text: str) -> list[float]:
    text = text or ""
    fired = scan(text)
    fired_ids = {f.id for f in fired}

    row: list[float] = [1.0 if r.id in fired_ids else 0.0 for r in RULES]

    n_flags = float(len(fired))
    flag_weight = float(sum(f.weight for f in fired))

    n_chars = len(text)
    letters = [c for c in text if c.isalpha()]
    n_letters = len(letters)
    n_upper = sum(1 for c in letters if c.isupper())
    n_digits = len(_RE_DIGIT.findall(text))

    row.extend([
        n_flags,
        flag_weight,
        float(np.log1p(n_chars)),
        float(np.log1p(len(text.split()))),
        (n_upper / n_letters) if n_letters else 0.0,
        (n_digits / n_chars) if n_chars else 0.0,
        float(min(text.count("!"), 10)),
        float(min(len(_RE_UPPER_WORD.findall(text)), 10)),
        1.0 if _RE_URL.search(text) else 0.0,
        float(min(len(_RE_MONEY.findall(text)), 10)),
        1.0 if _RE_PHONE.search(text) else 0.0,
    ])
    return row


class NumericFeatureExtractor:
    """Stateless scikit-learn-style transformer: text -> dense feature matrix.

    Implements the minimal estimator API (``fit``/``transform``/
    ``get_feature_names_out``) and ``get_params``/``set_params`` so it works
    inside ``Pipeline``/``FeatureUnion`` and pickles cleanly. It holds no
    learned state — every feature is computed deterministically from the text.
    """

    def fit(self, X=None, y=None):  # noqa: N803 (sklearn arg name)
        return self

    def transform(self, X):  # noqa: N803
        return np.asarray([_features_for(t) for t in X], dtype=np.float64)

    def fit_transform(self, X, y=None):  # noqa: N803
        return self.transform(X)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(FEATURE_NAMES, dtype=object)

    # Needed so sklearn can clone/persist the step.
    def get_params(self, deep=True):
        return {}

    def set_params(self, **params):
        return self
