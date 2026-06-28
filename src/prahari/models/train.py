"""Train the scam detector and persist a self-describing model artifact.

The artifact written to ``models/prahari_model.joblib`` bundles the fitted
pipeline together with everything needed to score and to *reproduce the exact
evaluation split*: the class order, the index of the ``scam`` class in
``predict_proba``, and the split parameters (seed + test fraction). That lets
:mod:`prahari.models.evaluate` re-derive the held-out set without us having to
serialise the data.

If no unified dataset exists yet (e.g. the Kaggle CSVs haven't been
downloaded), training falls back to a synthetic-only corpus so the whole
pipeline is runnable out of the box — with a loud warning, because a model
trained only on synthetic data is a demo, not a production detector.
"""
from __future__ import annotations

import datetime as _dt
import warnings
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from prahari import config
from prahari.models.pipeline import build_pipeline

MODEL_PATH: Path = config.MODELS_DIR / "prahari_model.joblib"

DEFAULT_TEST_SIZE = 0.2
MIN_ROWS = 50  # below this a train/test split is meaningless


def _load_training_frame() -> pd.DataFrame:
    """Load the unified dataset, or synthesise one if it's missing/too small."""
    if config.PROCESSED_DATASET.exists():
        df = pd.read_csv(config.PROCESSED_DATASET)
        df = df.dropna(subset=["text", "label"])
        df = df[df["label"].isin(config.LABELS)]
        if len(df) >= MIN_ROWS and df["label"].nunique() == 2:
            return df.reset_index(drop=True)
        warnings.warn(
            f"Unified dataset at {config.PROCESSED_DATASET} has only {len(df)} "
            "usable rows; falling back to synthetic-only data for this run."
        )
    else:
        warnings.warn(
            "No unified dataset found. Training on SYNTHETIC data only — run "
            "`prahari augment` (after adding Kaggle CSVs to data/raw) for a real "
            "model. This run is a functional demo."
        )
    from prahari.generator import generate
    return generate(n_scam=600, n_legit=600, seed=config.RANDOM_SEED)


def train(
    out_path: Optional[Path] = None,
    test_size: float = DEFAULT_TEST_SIZE,
    seed: int = config.RANDOM_SEED,
) -> dict:
    """Fit the pipeline, report held-out metrics, and save the artifact.

    Returns a summary dict (also printed). The held-out metrics here are a
    quick sanity check; :mod:`prahari.models.evaluate` produces the full report.
    """
    config.ensure_dirs()
    config.set_global_seed(seed)
    out_path = out_path or MODEL_PATH

    df = _load_training_frame()
    X = df["text"].astype(str).tolist()
    y = df["label"].astype(str).tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y,
    )

    print(f"Training on {len(X_train)} rows, holding out {len(X_test)} for test…")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    classes = list(pipe.named_steps["clf"].classes_)
    scam_index = classes.index(config.LABEL_SCAM)

    proba = pipe.predict_proba(X_test)[:, scam_index]
    y_pred = pipe.predict(X_test)
    y_true_bin = np.asarray([1 if v == config.LABEL_SCAM else 0 for v in y_test])

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_scam": round(float(f1_score(y_true_bin, (proba >= 0.5).astype(int))), 4),
        "roc_auc": round(float(roc_auc_score(y_true_bin, proba)), 4),
    }

    artifact = {
        "pipeline": pipe,
        "classes": classes,
        "scam_index": scam_index,
        "version": config.__dict__.get("__version__", "0.1.0"),
        "trained_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "split": {"test_size": test_size, "seed": seed},
        "sources": df["source"].value_counts().to_dict() if "source" in df else {},
        "holdout_metrics": metrics,
    }
    joblib.dump(artifact, out_path)

    print("\n================ Training complete ================")
    print(f"  rows total      : {len(df)}")
    print(f"  sources         : {artifact['sources']}")
    print(f"  accuracy        : {metrics['accuracy']}")
    print(f"  F1 (scam)       : {metrics['f1_scam']}")
    print(f"  ROC-AUC         : {metrics['roc_auc']}")
    print(f"  saved model ->    {out_path}")
    print("===================================================")
    return artifact


if __name__ == "__main__":  # pragma: no cover
    train()
