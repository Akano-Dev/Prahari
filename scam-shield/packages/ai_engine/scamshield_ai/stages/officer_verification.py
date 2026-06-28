"""Stage 8 — officer-claim verification (behaviour-consistency, not identity).

If the caller claims to represent a government agency, we extract the claimed
name / department / designation / location from the entities, then judge whether
their **requests and behaviour** are consistent with how a real official
operates — using the knowledge base's "red lines". We never assert the caller's
true identity; we flag *impossible* claims (e.g. an agency arresting over a video
call and demanding UPI) as the scam tell they are.
"""
from __future__ import annotations

import json
from importlib import resources

from ..context import ConversationState

_AGENCY_KEYS = {
    "cbi": "cbi", "central bureau": "cbi",
    "ed": "ed", "enforcement directorate": "ed",
    "rbi": "rbi", "reserve bank": "rbi",
    "police": "police", "cyber cell": "police", "cyber crime": "police",
    "trai": "trai", "customs": "customs",
}


def _load_agencies() -> dict:
    return json.loads(
        resources.files("scamshield_ai.knowledge").joinpath("agencies.json").read_text("utf-8"))


class OfficerVerificationStage:
    name = "officer_verification"

    def __init__(self):
        self._kb = _load_agencies()

    def process(self, utterance: str, state: ConversationState) -> None:
        ent = {e.type: e for e in state.entities}
        agency_ent = next((e for e in state.entities if e.type == "AGENCY"), None)
        if not agency_ent and state.behaviour.get("authority_impersonation", 0) < 0.5:
            return  # no government claim in play

        oc = state.officer
        oc.claimed = True
        if agency_ent:
            oc.department = agency_ent.value
        oc.name = ent.get("PERSON").value if "PERSON" in ent else oc.name
        oc.designation = ent.get("DESIGNATION").value if "DESIGNATION" in ent else oc.designation
        oc.location = ent.get("LOCATION").value if "LOCATION" in ent else oc.location

        # Consistency verdict from observed behaviour vs. universal red lines.
        impossible = []
        b = state.behaviour
        sig = set(state.signals)
        if "digital_arrest" in sig:
            impossible.append("Claims a 'digital arrest' — not a real legal procedure.")
        if b.get("money_request", 0) >= 0.5:
            impossible.append("Demands a money transfer — no agency does this over a call.")
        if b.get("credential_request", 0) >= 0.5:
            impossible.append("Asks for OTP/bank details — officials never do.")
        if b.get("video_call_pressure", 0) >= 0.5:
            impossible.append("Pushes a video-call interrogation — agencies don't operate this way.")
        if b.get("secrecy", 0) >= 0.5:
            impossible.append("Demands secrecy from family — a coercion tactic, not procedure.")

        oc.notes = impossible or oc.notes
        if impossible:
            oc.consistency = "impossible"
        elif oc.claimed:
            oc.consistency = "suspicious"
        else:
            oc.consistency = "unknown"

        if impossible and not any(t.kind == "officer" for t in state.timeline):
            state.add_timeline("officer", "Officer claim inconsistent with real procedure",
                               detail=impossible[0])
