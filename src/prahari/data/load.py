"""Load the raw Kaggle corpora and unify them into one scam-vs-legit dataset.

Design goals (see project brief):

* **Tolerant.** Kaggle exports differ in filename, encoding and column names.
  We search for files by glob, sniff the encoding, and *detect* the text and
  label columns from hints + heuristics rather than hard-coding indices.
* **Non-fatal.** A missing/unreadable source is skipped with a clear warning,
  never a crash — you can build a partial dataset from whatever is present.
* **Transparent.** Every row keeps a ``source`` tag so the EDA notebook can
  show where the data came from and per-source class balance.

Output schema written to ``data/processed/dataset.csv``::

    text,label,source
    "...message text...",scam|legit,<source-key>

Run via the CLI::

    python -m prahari.cli build-data
"""
from __future__ import annotations

import unicodedata
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from prahari import config
from prahari.config import DatasetSpec

# Encodings tried, in order, when reading a CSV (covers the classic latin-1
# SMS file and modern utf-8 exports, with a permissive last resort).
_ENCODINGS = ("utf-8", "latin-1", "utf-8-sig", "cp1252")


# --------------------------------------------------------------------------- #
# Text cleaning
# --------------------------------------------------------------------------- #
def clean_text(value: object) -> str:
    """Normalise a single text cell.

    NFKC-normalise unicode, drop control characters, turn any run of
    whitespace (incl. newlines/tabs) into a single space, and strip. Casing is
    intentionally preserved — TF-IDF lowercases downstream, and the red-flag
    engine benefits from seeing original case (e.g. "URGENT", "CBI").
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = str(value)
    s = unicodedata.normalize("NFKC", s)
    # Remove control chars except normal whitespace, which we collapse next.
    s = "".join(ch for ch in s if ch == " " or unicodedata.category(ch)[0] != "C")
    s = " ".join(s.split())
    return s.strip()


# --------------------------------------------------------------------------- #
# File discovery
# --------------------------------------------------------------------------- #
def _find_file(spec: DatasetSpec, raw_dir: Path) -> Optional[Path]:
    """Return the first file in ``raw_dir`` matching any of the spec globs.

    Matching is case-insensitive (Kaggle filenames vary in case). Direct
    filename matches are preferred over wildcard matches.
    """
    if not raw_dir.exists():
        return None
    candidates = [p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".csv"]
    names = {p: p.name.lower() for p in candidates}
    for pattern in spec.filename_globs:
        pat = pattern.lower()
        # Exact name first.
        for p, name in names.items():
            if name == pat:
                return p
        # Then glob.
        for p in candidates:
            if p.match(pattern) or Path(names[p]).match(pat):
                return p
    return None


def _read_csv_tolerant(path: Path, spec: DatasetSpec) -> Optional[pd.DataFrame]:
    """Read a CSV trying several encodings; warn and return None on failure."""
    preferred = spec.read_csv_kwargs.get("encoding")
    order = ([preferred] if preferred else []) + [e for e in _ENCODINGS if e != preferred]
    kwargs = {k: v for k, v in spec.read_csv_kwargs.items() if k != "encoding"}
    last_err: Optional[Exception] = None
    for enc in order:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception as err:  # pragma: no cover - depends on file content
            last_err = err
    warnings.warn(f"[{spec.key}] could not read {path.name}: {last_err}")
    return None


# --------------------------------------------------------------------------- #
# Column detection
# --------------------------------------------------------------------------- #
def _norm(name: object) -> str:
    return str(name).strip().lower()


def _detect_text_column(df: pd.DataFrame, hints: tuple[str, ...]) -> Optional[str]:
    """Pick the message/body column by name hint, else by longest mean text."""
    lookup = {_norm(c): c for c in df.columns}
    for hint in hints:
        if _norm(hint) in lookup:
            return lookup[_norm(hint)]
    # Heuristic fallback: object column with the greatest average string length.
    best_col, best_len = None, -1.0
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue
        mean_len = series.astype(str).str.len().mean()
        if mean_len > best_len:
            best_col, best_len = col, mean_len
    return best_col


def _detect_label_column(
    df: pd.DataFrame, hints: tuple[str, ...], text_col: Optional[str]
) -> Optional[str]:
    """Pick the label column by name hint, else the lowest-cardinality column."""
    lookup = {_norm(c): c for c in df.columns}
    for hint in hints:
        if _norm(hint) in lookup:
            return lookup[_norm(hint)]
    # Heuristic fallback: among non-text columns, the one with the fewest
    # distinct non-null values (a 2-class label has very low cardinality).
    best_col, best_card = None, None
    for col in df.columns:
        if col == text_col:
            continue
        nun = df[col].dropna().nunique()
        if nun < 2:
            continue
        if best_card is None or nun < best_card:
            best_col, best_card = col, nun
    return best_col


# --------------------------------------------------------------------------- #
# Label normalisation
# --------------------------------------------------------------------------- #
def _label_token(value: object) -> str:
    """Normalise a raw label cell to a comparable token (handles 1.0 -> '1')."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip().lower()


def _normalize_label(value: object, spec: DatasetSpec) -> Optional[str]:
    """Map one raw label value to ``scam`` / ``legit`` (or None if unknown)."""
    token = _label_token(value)
    if not token:
        return None
    spec_map = {_label_token(k): v for k, v in spec.label_value_map.items()}
    if token in spec_map:
        return spec_map[token]
    if token in config.SCAM_TOKENS:
        return config.LABEL_SCAM
    if token in config.LEGIT_TOKENS:
        return config.LABEL_LEGIT
    return None


# --------------------------------------------------------------------------- #
# Per-source load
# --------------------------------------------------------------------------- #
def load_one(spec: DatasetSpec, raw_dir: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """Load and normalise a single source into ``[text, label, source]``.

    Returns ``None`` (with a warning) if the file is missing or no usable
    text/label columns can be identified.
    """
    raw_dir = raw_dir or config.RAW_DIR
    path = _find_file(spec, raw_dir)
    if path is None:
        warnings.warn(
            f"[{spec.key}] no file found in {raw_dir} matching {spec.filename_globs} "
            f"(download '{spec.kaggle_slug}' from Kaggle). Skipping."
        )
        return None

    df = _read_csv_tolerant(path, spec)
    if df is None or df.empty:
        warnings.warn(f"[{spec.key}] {path.name} is empty/unreadable. Skipping.")
        return None

    text_col = _detect_text_column(df, spec.text_col_hints)
    label_col = _detect_label_column(df, spec.label_col_hints, text_col)
    if text_col is None or label_col is None:
        warnings.warn(
            f"[{spec.key}] could not detect text/label columns in {path.name} "
            f"(columns={list(df.columns)}). Skipping."
        )
        return None

    out = pd.DataFrame({
        "text": df[text_col].map(clean_text),
        "label": df[label_col].map(lambda v: _normalize_label(v, spec)),
    })
    out["source"] = spec.key

    n_raw = len(out)
    unmapped = int(out["label"].isna().sum())
    out = out[out["label"].notna()]
    out = out[out["text"].str.len() >= config.MIN_TEXT_LEN]
    n_kept = len(out)

    print(
        f"[{spec.key}] {path.name}: text='{text_col}', label='{label_col}' -> "
        f"{n_kept}/{n_raw} rows kept"
        + (f" ({unmapped} unmapped labels dropped)" if unmapped else "")
    )
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Unified build
# --------------------------------------------------------------------------- #
def load_all(
    raw_dir: Optional[Path] = None,
    specs: tuple[DatasetSpec, ...] = config.DATASET_SPECS,
) -> pd.DataFrame:
    """Load every available source and concatenate (no dedup yet)."""
    raw_dir = raw_dir or config.RAW_DIR
    frames = []
    for spec in specs:
        df = load_one(spec, raw_dir=raw_dir)
        if df is not None and not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["text", "label", "source"])
    return pd.concat(frames, ignore_index=True)


def build_dataset(
    raw_dir: Optional[Path] = None,
    out_path: Optional[Path] = None,
    extra: Optional[pd.DataFrame] = None,
    write: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Build the unified dataset and (optionally) write it to disk.

    Parameters
    ----------
    raw_dir : Path, optional
        Where the raw Kaggle CSVs live. Defaults to ``data/raw``.
    out_path : Path, optional
        Where to write the unified CSV. Defaults to ``data/processed/dataset.csv``.
    extra : DataFrame, optional
        Additional rows (e.g. the Phase-3 domain augmentation) with the same
        ``[text, label, source]`` schema, appended before dedup.
    write : bool
        If False, build in-memory only (used by tests).

    Returns
    -------
    (df, summary) : the unified DataFrame and a summary dict of counts.
    """
    raw_dir = raw_dir or config.RAW_DIR
    out_path = out_path or config.PROCESSED_DATASET

    df = load_all(raw_dir=raw_dir)
    if extra is not None and not extra.empty:
        extra = extra.copy()
        for col in ("text", "label", "source"):
            if col not in extra.columns:
                raise ValueError(f"`extra` is missing required column '{col}'")
        df = pd.concat([df, extra[["text", "label", "source"]]], ignore_index=True)

    n_before = len(df)
    if n_before:
        # Final clean + case-insensitive dedup (keep first occurrence).
        df["text"] = df["text"].map(clean_text)
        df = df[df["text"].str.len() >= config.MIN_TEXT_LEN]
        df = df[df["label"].isin(config.LABELS)]
        dedup_key = df["text"].str.lower()
        df = df[~dedup_key.duplicated(keep="first")].reset_index(drop=True)
    n_after = len(df)

    summary = _summarize(df, n_before=n_before, n_after=n_after)

    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        summary["written_to"] = str(out_path)
        print(f"\nWrote {n_after} rows -> {out_path}")

    _print_summary(summary)
    return df, summary


def _summarize(df: pd.DataFrame, n_before: int, n_after: int) -> dict:
    if df.empty:
        return {
            "rows_before_dedup": n_before,
            "rows": 0,
            "duplicates_removed": n_before,
            "by_label": {},
            "by_source": {},
            "by_source_label": {},
        }
    by_label = df["label"].value_counts().to_dict()
    by_source = df["source"].value_counts().to_dict()
    by_source_label = (
        df.groupby(["source", "label"]).size().unstack(fill_value=0).to_dict("index")
    )
    return {
        "rows_before_dedup": n_before,
        "rows": n_after,
        "duplicates_removed": n_before - n_after,
        "by_label": by_label,
        "by_source": by_source,
        "by_source_label": {k: dict(v) for k, v in by_source_label.items()},
    }


def _print_summary(summary: dict) -> None:
    print("\n================ Unified dataset summary ================")
    print(f"rows: {summary['rows']}  (removed {summary['duplicates_removed']} dup/empty)")
    if summary["by_label"]:
        total = max(summary["rows"], 1)
        for label, n in sorted(summary["by_label"].items()):
            print(f"  {label:<6}: {n:>7}  ({100 * n / total:5.1f}%)")
    if summary["by_source"]:
        print("  by source:")
        for src, n in sorted(summary["by_source"].items()):
            print(f"    {src:<16}: {n:>7}")
    print("========================================================")


def load_processed(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the unified dataset written by :func:`build_dataset`."""
    path = path or config.PROCESSED_DATASET
    if not path.exists():
        raise FileNotFoundError(
            f"No unified dataset at {path}. Run `python -m prahari.cli build-data` first."
        )
    return pd.read_csv(path)


if __name__ == "__main__":  # pragma: no cover
    config.ensure_dirs()
    config.set_global_seed()
    build_dataset()
