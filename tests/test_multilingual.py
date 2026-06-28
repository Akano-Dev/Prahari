"""Tests for Hindi / Hinglish (romanized + Devanagari) coverage.

Real digital-arrest scripts targeting Indian victims are frequently *not* in
English. These tests pin the behaviour that the same tactics are caught — and
that benign Hindi/Hinglish chatter stays quiet — so the multilingual patterns
can't silently regress.
"""
from __future__ import annotations

from prahari.features.red_flags import rule_score, scan
from prahari.generator import generate
from prahari.models.predict import DECISION_THRESHOLD, predict

# A romanized-Hindi ("Hinglish") digital-arrest script.
HINGLISH_SCAM = (
    "Inspector Sharma CBI se bol raha hoon. Aapke parcel mein MDMA mila hai, aap "
    "ab digital arrest mein hain. Phone band mat karo aur kisi ko mat batao. "
    "Rs 50,000 safe account mein turant transfer karo aur OTP bhejo warna "
    "giraftari ho jayegi."
)

# The same scam written in Devanagari.
DEVANAGARI_SCAM = (
    "सीबीआई: आप डिजिटल अरेस्ट में हैं। किसी को मत बताएं। 50000 रुपये सुरक्षित "
    "खाते में तुरंत ट्रांसफर करें वरना गिरफ्तारी होगी। सत्यापन के लिए ओटीपी भेजें।"
)

# Benign Hinglish chat that must NOT be flagged.
HINGLISH_LEGIT = (
    "Maa main hostel safely pahunch gaya. Train mein network nahi tha. Aaj raat "
    "khaane ke baad video call karunga. Love you."
)


def test_hinglish_scam_fires_decisive_flags():
    fired = {f.id for f in scan(HINGLISH_SCAM)}
    for expected in ("digital_arrest", "authority_impersonation",
                     "money_demand", "credential_request", "secrecy_isolation"):
        assert expected in fired, f"expected {expected} to fire on Hinglish scam"
    assert rule_score(HINGLISH_SCAM) > 0.7


def test_devanagari_scam_fires_decisive_flags():
    fired = {f.id for f in scan(DEVANAGARI_SCAM)}
    for expected in ("digital_arrest", "money_demand",
                     "credential_request", "secrecy_isolation"):
        assert expected in fired, f"expected {expected} to fire on Devanagari scam"
    assert rule_score(DEVANAGARI_SCAM) > 0.7


def test_hinglish_legit_stays_quiet():
    assert scan(HINGLISH_LEGIT) == []
    assert rule_score(HINGLISH_LEGIT) == 0.0


def test_multilingual_scams_predicted_as_scam():
    for text in (HINGLISH_SCAM, DEVANAGARI_SCAM):
        r = predict(text)
        assert r["is_scam"] is True
        assert r["score"] >= DECISION_THRESHOLD
        assert r["red_flags"]


def test_hinglish_legit_predicted_safe():
    r = predict(HINGLISH_LEGIT)
    assert r["is_scam"] is False
    assert r["score"] < DECISION_THRESHOLD


def test_generator_emits_multilingual_examples():
    df = generate(n_scam=120, n_legit=120, seed=11)
    # At least one romanized-Hindi and one Devanagari row should appear.
    blob = "\n".join(df["text"])
    assert "digital arrest mein" in blob.lower() or "transfer karo" in blob.lower()
    assert any("ऀ" <= ch <= "ॿ" for ch in blob), "expected Devanagari text"
