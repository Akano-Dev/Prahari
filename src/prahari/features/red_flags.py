"""Explainable red-flag rule engine for digital-arrest scams.

This module is the transparent backbone of Prahari. It scans a message or
call transcript for the tactics fraudsters use in "digital arrest" scams and
returns the concrete reasons a message looks dangerous. The model layer
(Phase 4) fuses this rule score with an ML probability, but the *explanation*
shown to a user always comes from here — so a non-technical person can see
exactly which red flags fired.

Each :class:`RedFlag` is a named, weighted rule backed by one or more regex
patterns. ``scan(text)`` returns the flags that fired (with the snippet that
triggered them); ``rule_score(text)`` collapses that into a 0..1 risk score.

Design notes
------------
* Patterns are compiled once at import, case-insensitive.
* Weights are *severity* hints (1=weak signal, 3=strong/near-decisive). They
  are combined with a saturating function so that two or three strong,
  independent flags already push the score high, mirroring how a human spots
  these scams.
* Adding a rule is a one-line edit to ``RULES`` — keep them
  human-readable; the ``description`` is shown verbatim to end users.
* **Multilingual.** Real digital-arrest scripts targeting Indian victims are
  frequently in romanized Hindi ("Hinglish") or Devanagari — e.g. "paise
  transfer karo, OTP bhejo, warna giraftari ho jayegi" or
  "आप डिजिटल अरेस्ट में हैं". Each rule therefore carries English *and*
  Hindi/Hinglish patterns so the same tactic is caught regardless of language.
  ``\b`` word boundaries are dropped around Devanagari fragments (the literals
  are distinctive enough), and only unambiguous romanized tokens are used to
  avoid colliding with English/proper nouns (e.g. we match "turant"/"warna"
  but not the name-like "abhi").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# --------------------------------------------------------------------------- #
# Rule definition
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RedFlag:
    """A single named, weighted detection rule.

    Parameters
    ----------
    id : str
        Stable machine id (snake_case) — used in features and the API.
    label : str
        Short human title, e.g. "Authority impersonation".
    description : str
        One-sentence plain-language explanation shown to the user.
    weight : int
        Severity 1 (weak) .. 3 (near-decisive).
    patterns : tuple[str, ...]
        Regex fragments; the rule fires if *any* matches (case-insensitive).
    """
    id: str
    label: str
    description: str
    weight: int
    patterns: tuple[str, ...]
    _compiled: tuple[re.Pattern, ...] = field(default=(), compare=False, repr=False)

    def compiled(self) -> tuple[re.Pattern, ...]:
        # Lazily compile and cache on the (frozen) instance.
        if not self._compiled:
            object.__setattr__(
                self, "_compiled",
                tuple(re.compile(p, re.IGNORECASE) for p in self.patterns),
            )
        return self._compiled

    def search(self, text: str) -> str | None:
        """Return the first matching snippet, or None if the rule didn't fire."""
        for pat in self.compiled():
            m = pat.search(text)
            if m:
                return m.group(0)
        return None


@dataclass(frozen=True)
class FiredFlag:
    """A rule that matched, plus the snippet that triggered it."""
    id: str
    label: str
    description: str
    weight: int
    match: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "weight": self.weight,
            "match": self.match,
        }


# --------------------------------------------------------------------------- #
# The rule set — ordered roughly by how decisive the tactic is.
# --------------------------------------------------------------------------- #
RULES: tuple[RedFlag, ...] = (
    RedFlag(
        id="digital_arrest",
        label="'Digital arrest' / custody language",
        description=(
            "Mentions a 'digital arrest', online custody or a warrant served "
            "over a call. 'Digital arrest' is not a real legal procedure — no "
            "agency arrests anyone over a video call."
        ),
        weight=3,
        patterns=(
            r"\bdigital\s+arrest\b",
            r"\bonline\s+arrest\b",
            r"\barrest\s+warrant\b",
            r"\bnon[-\s]?bailable\b",
            r"\byou\s+are\s+under\s+(?:digital\s+)?arrest\b",
            r"\b(?:judicial\s+)?(?:remand|custody)\b",
            # Hinglish / Devanagari
            r"\bdigital\s+arrest\s+(?:mein|me|hain?|ho)\b",
            r"\bgiraftar?i?\b",            # giraftar / giraftari / giraftaar
            r"डिजिटल\s*अरेस्ट",
            r"गिरफ्तार|गिरफ़्तार|गिरफ्तारी",
            r"हिरासत",                     # custody
        ),
    ),
    RedFlag(
        id="authority_impersonation",
        label="Authority impersonation",
        description=(
            "Claims to be police, CBI, ED, RBI, customs, TRAI, narcotics or "
            "another agency. Real officials don't conduct investigations or "
            "demand money over WhatsApp/phone."
        ),
        weight=3,
        patterns=(
            # Couriers (FedEx/DHL) are intentionally NOT here — they belong to
            # the parcel hook, not authority impersonation.
            r"\b(?:CBI|RBI|TRAI)\b",
            r"\bED\b(?=.*\b(?:case|arrest|money\s+laundering|notice)\b)",
            r"\benforcement\s+directorate\b",
            r"\bcyber\s*crime\b",
            r"\bnarcotics?\b",
            r"\bcustoms?\s+(?:department|official|officer)\b",
            r"\bincome\s+tax\s+department\b",
            r"\b(?:police|inspector|sub[-\s]?inspector|constable|officer)\b",
            r"\bmumbai\s+police\b|\bdelhi\s+police\b|\bcyber\s+cell\b",
            # Hinglish / Devanagari
            r"पुलिस|सीबीआई|ईडी\b|साइबर\s*क्राइम|नार्कोटिक्स|कस्टम",
            r"\bthana\b|\bthane\s+se\b",   # police station
        ),
    ),
    RedFlag(
        id="money_demand",
        label="Demand to transfer money",
        description=(
            "Asks you to pay a fine, penalty, 'security deposit' or to move "
            "money to a 'safe'/'RBI verification' account. No agency asks you "
            "to transfer money to prove innocence."
        ),
        weight=3,
        patterns=(
            r"\bsafe\s+(?:custody\s+)?account\b",
            r"\bsecurity\s+deposit\b",
            r"\bverification\s+(?:fee|charge|deposit)\b",
            r"\bclearance\s+(?:fee|charge)\b",
            r"\bprove\s+your\s+innocence\b",
            r"\b(?:transfer|deposit|pay|remit|send)\b[^.]{0,40}\b(?:money|amount|funds?|rs\.?|inr|rupees?|₹|lakhs?|crores?)\b",
            r"\b(?:RTGS|NEFT|IMPS|UPI)\b",
            r"\bfine\s+of\b|\bpenalty\s+of\b",
            # Hinglish / Devanagari
            r"\bpaise?\s+(?:transfer|bhej|jama|de\s+do|deposit)",
            r"\b(?:transfer|jama)\s+kar(?:o|do|en|na|iye)?\b",
            r"\bsafe\s+account\s+(?:mein|me)\b",
            r"पैसे?\s*(?:ट्रांसफर|भेज|जमा)|ट्रांसफर\s*कर|रुपये\s*(?:भेज|जमा)",
            r"सुरक्षित\s*(?:खाते|अकाउंट)",
        ),
    ),
    RedFlag(
        id="credential_request",
        label="Requests OTP / bank / ID details",
        description=(
            "Asks for an OTP, CVV, PIN, full card/bank number, Aadhaar or PAN. "
            "Legitimate officials and banks never ask for these."
        ),
        weight=3,
        patterns=(
            r"\bOTP\b",
            r"\bone[-\s]?time\s+password\b",
            r"\bCVV\b",
            r"\b(?:ATM\s+)?PIN\b",
            r"\bcard\s+number\b",
            r"\b(?:bank\s+)?account\s+(?:number|details)\b",
            r"\bAadhaar\b|\bAadhar\b|\bPAN\s+(?:card|number)\b",
            # Hinglish / Devanagari
            r"\bOTP\s+(?:bhej|bata|share\s+kar|do)",
            r"ओटीपी|आधार\s*(?:नंबर|कार्ड)?|पैन\s*कार्ड",
            r"\bbank\s+detail(?:s)?\s+(?:bhej|do|bata)",
        ),
    ),
    RedFlag(
        id="secrecy_isolation",
        label="Secrecy / stay-on-the-call pressure",
        description=(
            "Tells you to keep it confidential, not tell family, or to stay on "
            "the call/video. Isolation is a core coercion tactic of this scam."
        ),
        weight=2,
        patterns=(
            r"\bdo\s+not\s+(?:tell|inform|disclose)\b",
            r"\bdon'?t\s+(?:tell|inform|disclose)\b",
            r"\bkeep\s+(?:this|it)\s+confidential\b",
            r"\bstay\s+on\s+the\s+(?:call|line)\b",
            r"\bdo\s+not\s+(?:disconnect|hang\s+up|cut\s+the\s+call)\b",
            r"\bremain\s+available\b",
            r"\bunder\s+(?:surveillance|investigation)\b",
            # Hinglish / Devanagari
            r"\bkisi\s+ko\s+(?:mat|na|nahi)\s+bata",
            r"\b(?:phone|call|line)\s+(?:band|disconnect|cut|kaat)\s*(?:mat|nahi)",
            r"\bcall\s+(?:pe|par)\s+(?:bane?\s+raho|raho)",
            r"किसी\s+को\s+(?:मत|नहीं)\s+बता",
            r"फ़?ोन\s+(?:बंद|काट)\s+मत|कॉल\s+मत\s+काट",
        ),
    ),
    RedFlag(
        id="urgency_threat",
        label="Urgency / legal threat",
        description=(
            "Creates extreme time pressure or threatens immediate arrest, FIR "
            "or account freeze. Pressure to act 'right now' stops you checking."
        ),
        weight=2,
        patterns=(
            r"\bimmediately\b",
            r"\bwithin\s+\d+\s*(?:hours?|minutes?|hrs?|min)\b",
            r"\b(?:final|last)\s+(?:notice|warning)\b",
            r"\blegal\s+action\b",
            r"\bFIR\b|\bF\.?I\.?R\.?\b",
            r"\baccount\s+(?:will\s+be\s+)?(?:freez|block|suspend)",
            r"\bact\s+now\b|\burgent(?:ly)?\b",
            # Hinglish / Devanagari (unambiguous tokens only)
            r"\bturant\b|\bjaldi\s+karo\b|\bwarna\b",
            r"तुरंत|अभी\s+करें|वरना|जल्दी\s+करो",
        ),
    ),
    RedFlag(
        id="video_call_platform",
        label="Move to WhatsApp / Skype video",
        description=(
            "Pushes the conversation onto a WhatsApp/Skype video call to "
            "impersonate an officer in uniform / fake police station."
        ),
        weight=2,
        patterns=(
            r"\bwhats\s*app\s+(?:video\s+)?call\b",
            r"\bskype\s+(?:video\s+)?call\b",
            r"\bjoin\s+(?:the\s+)?video\s+call\b",
            r"\bvideo\s+(?:call|conference)\b[^.]{0,30}\b(?:officer|police|interrogat)",
            # Hinglish / Devanagari
            r"\bvideo\s+call\s+(?:pe|par|join)",
            r"वीडियो\s*कॉल",
        ),
    ),
    RedFlag(
        id="parcel_hook",
        label="Suspicious parcel / courier hook",
        description=(
            "Opens with a 'parcel held by customs' containing drugs, fake "
            "passports or illegal items — a common entry point to the scam."
        ),
        weight=2,
        patterns=(
            r"\b(?:parcel|package|courier|consignment|shipment)\b",
            r"\bseized\s+(?:by\s+)?customs\b",
            r"\bcontains?\s+(?:drugs?|narcotics?|illegal|contraband|MDMA|passport)\b",
            # Hinglish / Devanagari
            r"पार्सल|कूरियर|कुरियर",
            r"\bparcel\s+(?:mein|me)\b.{0,30}(?:drugs?|MDMA)",
        ),
    ),
    RedFlag(
        id="case_reference",
        label="Fake case / reference number",
        description=(
            "Quotes an official-sounding case, FIR or reference number to seem "
            "legitimate. Genuine notices arrive in writing, not over a call."
        ),
        weight=1,
        patterns=(
            r"\bcase\s+(?:id|no\.?|number|ref)\b",
            r"\bcomplaint\s+(?:no\.?|number)\b",
            r"\breference\s+(?:no\.?|number|code)\b",
            r"\bDD[-\s]?\d{2,}\b",
        ),
    ),
    RedFlag(
        id="suspicious_link",
        label="Suspicious link",
        description=(
            "Contains a link to click. Scam links impersonate official portals "
            "to harvest details or push remote-access apps."
        ),
        weight=1,
        patterns=(
            r"https?://\S+",
            r"\bwww\.\S+",
            r"\b(?:bit\.ly|tinyurl|t\.me|rb\.gy|cutt\.ly)/\S+",
        ),
    ),
)

# id -> RedFlag, for quick lookup elsewhere.
RULES_BY_ID = {r.id: r for r in RULES}
MAX_WEIGHT = sum(r.weight for r in RULES)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def scan(text: str, rules: Iterable[RedFlag] = RULES) -> list[FiredFlag]:
    """Return every rule that fires on ``text`` (order = RULES order)."""
    if not text:
        return []
    fired: list[FiredFlag] = []
    for rule in rules:
        match = rule.search(text)
        if match is not None:
            fired.append(FiredFlag(
                id=rule.id, label=rule.label, description=rule.description,
                weight=rule.weight, match=match.strip()[:120],
            ))
    return fired


def rule_score(text: str) -> float:
    """Collapse fired flags into a 0..1 risk score.

    Uses a saturating combination of severity weights rather than a raw sum,
    so a couple of strong, independent flags already score high while a single
    weak signal stays low. Concretely we sum the weights and squash with
    ``w / (w + k)`` where ``k`` is tuned so that weight≈4 (e.g. one weight-3
    flag plus a weak one) lands around 0.55 and weight≈8 around 0.75.
    """
    fired = scan(text)
    if not fired:
        return 0.0
    w = sum(f.weight for f in fired)
    k = 3.5
    return round(w / (w + k), 4)


def explain(text: str) -> dict:
    """Convenience bundle: score + the fired flags as plain dicts."""
    fired = scan(text)
    return {
        "rule_score": rule_score(text),
        "n_flags": len(fired),
        "flags": [f.to_dict() for f in fired],
    }
