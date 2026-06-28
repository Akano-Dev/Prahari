"""Central configuration for Prahari: paths, constants, seeds, dataset specs.

Everything path-related is derived from the repo root so the project works
regardless of the current working directory. Import this module rather than
hard-coding paths anywhere else.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
# config.py lives at: <root>/src/prahari/config.py  ->  parents[2] == <root>
ROOT_DIR: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = ROOT_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
INTERIM_DIR: Path = DATA_DIR / "interim"
PROCESSED_DIR: Path = DATA_DIR / "processed"
FIXTURES_DIR: Path = DATA_DIR / "fixtures"

MODELS_DIR: Path = ROOT_DIR / "models"
REPORTS_DIR: Path = ROOT_DIR / "reports"
NOTEBOOKS_DIR: Path = ROOT_DIR / "notebooks"

# The canonical unified dataset produced by data/load.py
PROCESSED_DATASET: Path = PROCESSED_DIR / "dataset.csv"

ALL_DIRS = [
    DATA_DIR, RAW_DIR, INTERIM_DIR, PROCESSED_DIR, FIXTURES_DIR,
    MODELS_DIR, REPORTS_DIR,
]


def ensure_dirs() -> None:
    """Create all standard project directories if they do not exist."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #
RANDOM_SEED: int = 42


def set_global_seed(seed: int = RANDOM_SEED) -> None:
    """Seed Python's ``random`` and (if importable) numpy for repeatable runs."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:  # numpy is a hard dep, but keep config import-light/defensive
        import numpy as np

        np.random.seed(seed)
    except Exception:  # pragma: no cover - numpy always present in practice
        pass


# --------------------------------------------------------------------------- #
# Label vocabulary — the unified schema is exactly two classes.
# --------------------------------------------------------------------------- #
LABEL_SCAM: str = "scam"
LABEL_LEGIT: str = "legit"
LABELS = (LABEL_SCAM, LABEL_LEGIT)

# How raw label tokens from the various Kaggle datasets map onto our two
# classes. Keys are compared lowercase/stripped. Numeric labels (0/1) are
# handled separately in the loader because their meaning is dataset-specific.
SCAM_TOKENS = frozenset({
    "scam", "spam", "fraud", "fraudulent", "phishing", "phishing email",
    "phish", "malicious", "smishing",
})
LEGIT_TOKENS = frozenset({
    "legit", "legitimate", "ham", "safe", "safe email", "normal", "not spam",
    "benign", "genuine", "real",
})

# --------------------------------------------------------------------------- #
# Risk bands — used by models/predict.py to turn a 0-100 score into a label.
# (Lower bound inclusive, upper bound inclusive.)
# --------------------------------------------------------------------------- #
RISK_BANDS = [
    (0, 24, "Safe"),
    (25, 49, "Suspicious"),
    (50, 74, "High Risk"),
    (75, 100, "Almost Certainly a Scam"),
]


def band_for_score(score: float) -> str:
    """Map a 0-100 risk score to its band label."""
    s = max(0.0, min(100.0, float(score)))
    for lo, hi, name in RISK_BANDS:
        if lo <= s <= hi:
            return name
    return RISK_BANDS[-1][2]


# --------------------------------------------------------------------------- #
# Dataset source specs (Phase 1)
#
# We do NOT hard-code exact filenames/column indices, because Kaggle exports
# vary. Each spec lists the Kaggle slug (for docs), candidate filename globs
# to look for inside data/raw/, and *hints* the loader uses to detect the text
# and label columns. The loader still falls back to heuristics if hints miss.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DatasetSpec:
    key: str                       # short internal id / source tag
    kaggle_slug: str               # e.g. "uciml/sms-spam-collection-dataset"
    filename_globs: tuple[str, ...]  # globs searched (case-insensitive) in raw/
    text_col_hints: tuple[str, ...]  # preferred text-column names
    label_col_hints: tuple[str, ...]  # preferred label-column names
    # Optional explicit value map for this dataset's label column. Useful for
    # numeric (0/1) labels whose polarity is dataset-specific.
    label_value_map: dict[str, str] = field(default_factory=dict)
    read_csv_kwargs: dict = field(default_factory=dict)
    note: str = ""


DATASET_SPECS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        key="sms_spam",
        kaggle_slug="uciml/sms-spam-collection-dataset",
        filename_globs=("spam.csv", "*sms*spam*.csv", "*spam*collection*.csv"),
        text_col_hints=("v2", "text", "message", "sms"),
        label_col_hints=("v1", "label", "class", "category"),
        # ham -> legit, spam -> scam (handled by token maps, listed for clarity)
        label_value_map={"ham": LABEL_LEGIT, "spam": LABEL_SCAM},
        read_csv_kwargs={"encoding": "latin-1"},  # this file is classic latin-1
        note="SMS spam vs ham — canonical base corpus.",
    ),
    DatasetSpec(
        key="fraud_email",
        kaggle_slug="llabhishekll/fraud-email-dataset",
        filename_globs=("fraud_email_.csv", "fraud_email*.csv", "*fraud*email*.csv"),
        text_col_hints=("text", "body", "email", "content"),
        label_col_hints=("class", "label", "target"),
        # This dataset uses numeric labels: 1 = fraudulent (scam), 0 = normal.
        label_value_map={"1": LABEL_SCAM, "0": LABEL_LEGIT},
        note="Fraudulent vs normal emails (numeric Class column: 1=fraud).",
    ),
    DatasetSpec(
        key="phishing_email",
        kaggle_slug="subhajournal/phishingemails",
        filename_globs=("Phishing_Email.csv", "*phishing*email*.csv", "*phishing*.csv"),
        text_col_hints=("email text", "text", "body", "email", "content"),
        label_col_hints=("email type", "type", "label", "class"),
        # "Phishing Email" -> scam, "Safe Email" -> legit
        label_value_map={"phishing email": LABEL_SCAM, "safe email": LABEL_LEGIT},
        note="Phishing vs safe emails.",
    ),
)

# Minimum cleaned text length (chars) to keep a row in the unified dataset.
MIN_TEXT_LEN: int = 3

# Cybercrime guidance shown to users (single source of truth for the app).
SAFE_ACTION_MESSAGE: str = (
    "Hang up / stop replying. No real police, CBI, ED, RBI or Cyber Crime "
    "official arrests you over WhatsApp or a video call, and none will ever "
    "ask you to transfer money to 'prove your innocence' or for 'safe "
    "custody'. Do not stay on the call and do not share OTPs or bank details. "
    "Report at https://cybercrime.gov.in or call the cyber helpline 1930."
)
