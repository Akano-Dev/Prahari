"""Stage 2 — Named Entity Recognition (regex baseline; spaCy-swappable).

Extracts the entities that matter for scam analysis and officer-claim checks:
agencies, designations, money amounts, phone numbers, OTPs, bank names, links,
case references, locations and person names. This deterministic extractor needs
no model; inject a spaCy-backed adapter for richer PERSON/GPE recall in
production (same output contract).
"""
from __future__ import annotations

import re

from ..context import ConversationState
from ..schemas import Entity

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AGENCY", re.compile(r"\b(CBI|RBI|ED|TRAI|Enforcement Directorate|Narcotics Control Bureau|"
                          r"Cyber Crime|Cyber Cell|Income Tax Department|Customs)\b", re.IGNORECASE)),
    ("DESIGNATION", re.compile(r"\b(Inspector|Sub[-\s]?Inspector|ASI|DCP|ACP|Officer|Constable|"
                               r"Commissioner)\b", re.IGNORECASE)),
    ("MONEY", re.compile(r"(?:₹|\bRs\.?\b|\bINR\b)\s?[\d,]+(?:\s?(?:lakh|crore)s?)?|"
                         r"\b\d+\s?(?:lakh|crore)s?\b", re.IGNORECASE)),
    ("OTP", re.compile(r"\bOTP\b|\bone[-\s]?time\s+password\b|\bCVV\b", re.IGNORECASE)),
    ("PHONE", re.compile(r"\b(?:\+?91[-\s]?)?\d{10}\b|\b1930\b")),
    ("BANK", re.compile(r"\b(HDFC|SBI|ICICI|Axis|Kotak|PNB|Bank of Baroda|Yes Bank)\b", re.IGNORECASE)),
    ("LINK", re.compile(r"https?://\S+|\bwww\.\S+|\b(?:bit\.ly|tinyurl|t\.me)/\S+", re.IGNORECASE)),
    ("CASE_REF", re.compile(r"\b(?:FIR|case|complaint|reference)\s+(?:no\.?|id|number|code)?\s*[:#]?\s*[A-Z0-9-]{3,}", re.IGNORECASE)),
    ("ID_DOC", re.compile(r"\bAadhaar\b|\bAadhar\b|\bPAN\b", re.IGNORECASE)),
]

# "Officer <FirstName> <LastName>" / "Inspector Sharma" style person capture.
_PERSON = re.compile(
    r"\b(?:Inspector|Sub[-\s]?Inspector|ASI|DCP|ACP|Officer|Constable|Mr\.?|Shri)\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)")
_LOCATION = re.compile(r"\b(Mumbai|Delhi|Bangalore|Bengaluru|Kolkata|Chennai|Hyderabad|Pune|"
                       r"Noida|Gurgaon|Gurugram|Jaipur|Lucknow)\b", re.IGNORECASE)


class NerStage:
    name = "ner"

    def process(self, utterance: str, state: ConversationState) -> None:
        idx = state.current_index
        seen = {(e.type, e.value.lower()) for e in state.entities}

        def add(etype: str, value: str) -> None:
            key = (etype, value.lower())
            if value and key not in seen:
                seen.add(key)
                state.entities.append(Entity(type=etype, value=value, utterance_index=idx))

        for etype, pat in _PATTERNS:
            for m in pat.finditer(utterance):
                add(etype, m.group(0).strip())
        for m in _PERSON.finditer(utterance):
            add("PERSON", m.group(1).strip())
        for m in _LOCATION.finditer(utterance):
            add("LOCATION", m.group(0).strip())
