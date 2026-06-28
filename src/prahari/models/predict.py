"""Score a message and explain *why* — the user-facing decision layer.

A final 0-100 risk score fuses two signals:

* ``ml_probability`` — the calibrated LogisticRegression probability of "scam".
* ``rule_score``     — the transparent red-flag engine (Phase 2).

``final = 100 * (ALPHA * ml_probability + (1 - ALPHA) * rule_score)``

Fusion matters because each signal covers the other's blind spot: the ML model
generalises to phrasings the rules miss, while the rule engine guarantees that
an obvious "you are under digital arrest, share the OTP" message scores high
even on a model trained on a thin corpus. The *explanation* always lists the
concrete red flags that fired, plus the official safe action.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import joblib

from prahari import config
from prahari.data.load import clean_text
from prahari.features.red_flags import rule_score, scan
from prahari.models.train import MODEL_PATH

# Weight on the ML probability vs. the rule engine in the fused score.
ALPHA = 0.65
# At/above this 0-100 score we call it a scam and surface the safe action.
DECISION_THRESHOLD = 50

# Safety floors driven by domain knowledge, not the (possibly under-trained)
# model. "Digital arrest" is the scam's signature — it is not a real legal
# procedure, so a legitimate message essentially never contains it. We refuse
# to let a weak ML probability bury that evidence, because for a defensive tool
# a missed scam (false negative) is the costly error. Floors never *lower* a
# score and never fire on text that lacks the signature flag, so they cannot
# raise the score of a genuinely benign message.
_SIGNATURE_FLAG = "digital_arrest"
_COERCION_FLAGS = {"money_demand", "credential_request", "authority_impersonation"}


def _safety_floor(fired_ids: set[str]) -> int:
    """Minimum score implied by decisive red-flag combinations (0 if none)."""
    if _SIGNATURE_FLAG in fired_ids and (fired_ids & _COERCION_FLAGS):
        return 75  # signature + a coercion demand = the scam's fingerprint
    if _SIGNATURE_FLAG in fired_ids:
        return 60
    return 0


@lru_cache(maxsize=4)
def load_model(path: Optional[str] = None) -> dict:
    """Load (and cache) the trained artifact written by :mod:`models.train`."""
    p = Path(path) if path else MODEL_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"No trained model at {p}. Run `prahari train` first."
        )
    return joblib.load(p)


def _ml_probability(text: str, artifact: dict) -> float:
    pipe = artifact["pipeline"]
    idx = artifact["scam_index"]
    return float(pipe.predict_proba([text])[0][idx])


def predict(text: str, model_path: Optional[str] = None) -> dict:
    """Score one message and return a structured, explainable verdict.

    The result is JSON-serialisable and is the single shape consumed by both
    the CLI and the FastAPI ``/score`` endpoint.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "input": text,
            "score": 0,
            "band": config.band_for_score(0),
            "is_scam": False,
            "ml_probability": 0.0,
            "rule_score": 0.0,
            "red_flags": [],
            "safe_action": config.SAFE_ACTION_MESSAGE,
            "explanation": "Empty message — nothing to score.",
        }

    artifact = load_model(model_path)
    ml_p = _ml_probability(cleaned, artifact)
    r_score = rule_score(cleaned)
    fused = ALPHA * ml_p + (1.0 - ALPHA) * r_score
    score = int(round(100 * fused))

    fired = scan(cleaned)
    score = max(score, _safety_floor({f.id for f in fired}))
    score = max(0, min(100, score))

    flags = [f.to_dict() for f in fired]
    is_scam = score >= DECISION_THRESHOLD

    if flags:
        top = ", ".join(f["label"] for f in flags[:3])
        explanation = (
            f"{len(flags)} red flag(s) detected — notably: {top}."
        )
    else:
        explanation = "No known scam red flags detected in the text."

    return {
        "input": text,
        "score": score,
        "band": config.band_for_score(score),
        "is_scam": is_scam,
        "ml_probability": round(ml_p, 4),
        "rule_score": round(r_score, 4),
        "red_flags": flags,
        "safe_action": config.SAFE_ACTION_MESSAGE,
        "explanation": explanation,
    }


def format_report(result: dict) -> str:
    """Render a :func:`predict` result as a readable CLI block."""
    lines = [
        "",
        "============== Prahari verdict ==============",
        f"  Risk score : {result['score']}/100  ({result['band']})",
        f"  Verdict    : {'⚠ LIKELY SCAM' if result['is_scam'] else 'Looks OK'}",
        f"  ML p(scam) : {result['ml_probability']}   rule score: {result['rule_score']}",
    ]
    if result["red_flags"]:
        lines.append("  Red flags:")
        for f in result["red_flags"]:
            lines.append(f"    • {f['label']}  (\"{f['match']}\")")
            lines.append(f"        {f['description']}")
    else:
        lines.append("  Red flags  : none")
    if result["is_scam"]:
        lines.append("")
        lines.append("  WHAT TO DO:")
        for chunk in _wrap(result["safe_action"], width=58):
            lines.append(f"    {chunk}")
    lines.append("=============================================")
    return "\n".join(lines)


def _wrap(text: str, width: int = 58) -> list[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out
