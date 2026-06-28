"""Tests for the explainable red-flag engine."""
from __future__ import annotations

from prahari.features.red_flags import RULES, RULES_BY_ID, explain, rule_score, scan

SCAM = (
    "This is CBI. You are under digital arrest. Transfer Rs 50000 to the safe "
    "account and share the OTP immediately. Do not tell anyone."
)
LEGIT = "Hey, are we still on for lunch tomorrow at 1pm? Let me know!"


def test_scam_fires_multiple_flags():
    fired = {f.id for f in scan(SCAM)}
    # The decisive tactics should all be detected.
    for expected in ("digital_arrest", "authority_impersonation",
                     "money_demand", "credential_request", "secrecy_isolation"):
        assert expected in fired, f"expected {expected} to fire"


def test_legit_message_is_quiet():
    assert scan(LEGIT) == []
    assert rule_score(LEGIT) == 0.0


def test_rule_score_orders_scam_above_legit():
    assert rule_score(SCAM) > 0.7
    assert rule_score(SCAM) > rule_score(LEGIT)


def test_empty_text_is_safe():
    assert scan("") == []
    assert rule_score("") == 0.0


def test_explain_shape():
    out = explain(SCAM)
    assert set(out) == {"rule_score", "n_flags", "flags"}
    assert out["n_flags"] == len(out["flags"]) > 0
    assert all({"id", "label", "description", "weight", "match"} <= set(f)
               for f in out["flags"])


def test_every_rule_has_unique_id_and_patterns():
    ids = [r.id for r in RULES]
    assert len(ids) == len(set(ids)) == len(RULES_BY_ID)
    assert all(r.patterns for r in RULES)
