"""Evaluate the trained model on a reproducible held-out split and write reports.

Re-derives the *same* test split the trainer held out (using the seed +
test_size stored in the artifact), then writes to ``reports/``:

* ``metrics.json``        — accuracy, precision/recall/F1, ROC-AUC, PR-AUC.
* ``confusion_matrix.png``
* ``roc_curve.png``

Matplotlib runs head-less (Agg) so this works on a server / CI with no display.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # headless: must be set before pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    ConfusionMatrixDisplay,
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split  # noqa: E402

from prahari import config  # noqa: E402
from prahari.models.predict import load_model  # noqa: E402
from prahari.models.train import _load_training_frame  # noqa: E402


def _reproduce_test_split(artifact: dict):
    """Rebuild the exact held-out test set used during training."""
    df = _load_training_frame()
    X = df["text"].astype(str).tolist()
    y = df["label"].astype(str).tolist()
    split = artifact.get("split", {"test_size": 0.2, "seed": config.RANDOM_SEED})
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=split["test_size"], random_state=split["seed"], stratify=y,
    )
    return X_test, y_test


def evaluate(model_path: Optional[str] = None, reports_dir: Optional[Path] = None) -> dict:
    config.ensure_dirs()
    reports_dir = reports_dir or config.REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)

    artifact = load_model(model_path)
    pipe = artifact["pipeline"]
    scam_index = artifact["scam_index"]

    X_test, y_test = _reproduce_test_split(artifact)
    y_true = np.asarray([1 if v == config.LABEL_SCAM else 0 for v in y_test])
    proba = pipe.predict_proba(X_test)[:, scam_index]
    y_pred = (proba >= 0.5).astype(int)

    report = classification_report(
        y_true, y_pred, target_names=[config.LABEL_LEGIT, config.LABEL_SCAM],
        output_dict=True, zero_division=0,
    )
    roc_auc = float(roc_auc_score(y_true, proba))
    pr_auc = float(average_precision_score(y_true, proba))

    metrics = {
        "n_test": int(len(y_true)),
        "accuracy": round(float(report["accuracy"]), 4),
        "precision_scam": round(float(report[config.LABEL_SCAM]["precision"]), 4),
        "recall_scam": round(float(report[config.LABEL_SCAM]["recall"]), 4),
        "f1_scam": round(float(report[config.LABEL_SCAM]["f1-score"]), 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "classification_report": report,
        "model_trained_at": artifact.get("trained_at"),
    }

    metrics_path = reports_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # --- Confusion matrix ---
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay(
        cm, display_labels=[config.LABEL_LEGIT, config.LABEL_SCAM]
    ).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Prahari — confusion matrix")
    fig.tight_layout()
    cm_path = reports_dir / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=120)
    plt.close(fig)

    # --- ROC curve ---
    fpr, tpr, _ = roc_curve(y_true, proba)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(fpr, tpr, label=f"ROC (AUC={roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", linewidth=1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Prahari — ROC curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    roc_path = reports_dir / "roc_curve.png"
    fig.savefig(roc_path, dpi=120)
    plt.close(fig)

    print("\n================ Evaluation ================")
    print(f"  test rows     : {metrics['n_test']}")
    print(f"  accuracy      : {metrics['accuracy']}")
    print(f"  precision/scam: {metrics['precision_scam']}")
    print(f"  recall/scam   : {metrics['recall_scam']}")
    print(f"  F1/scam       : {metrics['f1_scam']}")
    print(f"  ROC-AUC       : {metrics['roc_auc']}   PR-AUC: {metrics['pr_auc']}")
    print(f"  wrote         : {metrics_path.name}, {cm_path.name}, {roc_path.name}")
    print("============================================")
    return metrics


if __name__ == "__main__":  # pragma: no cover
    evaluate()
