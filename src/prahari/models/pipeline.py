"""The scikit-learn model pipeline.

A single ``Pipeline`` combines two complementary views of a message:

* **TF-IDF** word 1-2 grams — captures the vocabulary of scams vs. ham.
* **Numeric red-flag / structural features** — captures *how many* scam tactics
  fired plus casing, links, money and urgency (see
  :mod:`prahari.features.text_features`).

They are joined with a ``FeatureUnion`` and fed to a calibrated, class-balanced
``LogisticRegression`` which yields well-behaved probabilities for the score
fusion in :mod:`prahari.models.predict`.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import MaxAbsScaler

from prahari.features.text_features import NumericFeatureExtractor


def build_pipeline() -> Pipeline:
    """Construct (unfitted) the full text+numeric -> LogisticRegression pipeline."""
    tfidf = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        max_features=50_000,
    )
    numeric = Pipeline([
        ("extract", NumericFeatureExtractor()),
        # MaxAbsScaler keeps the matrix sparse-friendly (no centering) while
        # putting the hand-crafted features on a comparable scale to TF-IDF.
        ("scale", MaxAbsScaler()),
    ])
    features = FeatureUnion([
        ("tfidf", tfidf),
        ("numeric", numeric),
    ])
    clf = LogisticRegression(
        max_iter=2000,
        C=4.0,
        class_weight="balanced",
        n_jobs=None,
    )
    return Pipeline([("features", features), ("clf", clf)])
