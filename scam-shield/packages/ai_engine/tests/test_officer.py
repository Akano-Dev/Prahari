"""Tests for officer-claim verification and behaviour analysis."""
from __future__ import annotations

from scamshield_ai import AnalysisPipeline


def test_officer_claim_flagged_impossible():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text(
        "This is Inspector Verma from the CBI in Mumbai. You are under digital "
        "arrest. Transfer Rs 1,00,000 to the safe account and share the OTP.",
        call_id="call-officer")
    oc = a.officer_claim
    assert oc is not None and oc.claimed is True
    assert oc.consistency == "impossible"
    assert oc.department and "CBI" in oc.department.upper()
    assert oc.notes  # concrete reasons it's impossible


def test_behaviour_breakdown_populated():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text(
        "You are under digital arrest, transfer money now and share the OTP, "
        "do not tell anyone, this is urgent.")
    b = a.behaviour
    assert b.authority_impersonation > 0
    assert b.money_request > 0
    assert b.credential_request > 0
    assert b.secrecy > 0
    assert b.urgency > 0


def test_no_officer_claim_on_legit():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text("Your Amazon parcel will be delivered by 6 PM today.")
    assert a.officer_claim is None
