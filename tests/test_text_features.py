"""Tests for the numeric feature extractor."""
from __future__ import annotations

import numpy as np

from prahari.features.text_features import (
    FEATURE_NAMES,
    NumericFeatureExtractor,
)

SCAM = "URGENT! CBI: you are under DIGITAL ARREST. Transfer Rs 50000, share OTP now."
LEGIT = "see you at the cafe around five, no rush"


def test_matrix_shape_matches_feature_names():
    X = NumericFeatureExtractor().transform([SCAM, LEGIT])
    assert X.shape == (2, len(FEATURE_NAMES))
    assert X.dtype == np.float64


def test_feature_names_out_aligns():
    ext = NumericFeatureExtractor()
    names = list(ext.get_feature_names_out())
    assert names == FEATURE_NAMES


def test_scam_row_has_more_flag_signal():
    X = NumericFeatureExtractor().transform([SCAM, LEGIT])
    n_flags_idx = FEATURE_NAMES.index("n_flags")
    assert X[0, n_flags_idx] > X[1, n_flags_idx]


def test_transformer_is_sklearn_compatible():
    ext = NumericFeatureExtractor()
    # fit returns self; fit_transform works; params are empty (stateless).
    assert ext.fit([SCAM]) is ext
    assert ext.fit_transform([SCAM]).shape == (1, len(FEATURE_NAMES))
    assert ext.get_params() == {}
