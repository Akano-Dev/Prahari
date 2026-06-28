"""Tests for the prediction / score-fusion layer."""
from __future__ import annotations

from prahari import config
from prahari.models.predict import DECISION_THRESHOLD, format_report, predict

SCAM = (
    "This is the CBI cyber crime branch. You are under digital arrest in a "
    "money laundering case. Stay on the WhatsApp video call, transfer Rs "
    "1,20,000 to the safe account within 1 hour and share the OTP. Do not "
    "tell anyone."
)
LEGIT = "Reminder: your dentist appointment is tomorrow at 11am, please arrive early."


def test_scam_is_flagged_with_explanation():
    r = predict(SCAM)
    assert r["is_scam"] is True
    assert r["score"] >= DECISION_THRESHOLD
    assert r["red_flags"], "expected red flags on an obvious scam"
    assert r["safe_action"] == config.SAFE_ACTION_MESSAGE
    assert 0.0 <= r["ml_probability"] <= 1.0


def test_legit_is_not_flagged():
    r = predict(LEGIT)
    assert r["is_scam"] is False
    assert r["score"] < DECISION_THRESHOLD


def test_empty_input_scores_zero():
    r = predict("   ")
    assert r["score"] == 0
    assert r["is_scam"] is False
    assert r["red_flags"] == []


def test_result_is_json_serialisable_shape():
    r = predict(SCAM)
    expected = {
        "input", "score", "band", "is_scam", "ml_probability",
        "rule_score", "red_flags", "safe_action", "explanation",
    }
    assert expected <= set(r)
    assert isinstance(r["score"], int)
    assert r["band"] in {b[2] for b in config.RISK_BANDS}


def test_format_report_renders_safe_action_for_scam():
    report = format_report(predict(SCAM))
    assert "Prahari verdict" in report
    assert "WHAT TO DO" in report


def test_signature_safety_floor_resists_weak_ml():
    # An unusual phrasing the ML model may under-score, but with the scam's
    # signature ("digital arrest") + a money demand, must still rate High Risk.
    r = predict("Customs seized your parcel with drugs. You are under digital "
                "arrest, pay Rs 1 lakh.")
    assert r["score"] >= 75
    assert r["is_scam"] is True


def test_floor_does_not_fire_without_signature():
    # A benign message lacking the signature flag is unaffected by the floor.
    r = predict("Your India Post parcel is out for delivery this afternoon.")
    assert r["is_scam"] is False
    assert r["score"] < DECISION_THRESHOLD
