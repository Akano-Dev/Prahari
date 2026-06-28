"""Explainable multilingual red-flag rule engine (reused from Prahari).

This is the deterministic backbone of ScamShield: a transparent set of weighted,
named regex rules covering the tactics of digital-arrest and adjacent scams in
**English, romanized Hindi ("Hinglish") and Devanagari**. Each rule maps to a
behaviour bucket (urgency, fear, authority…) so the behaviour analysis and the
explainable signals come straight from here — no model required.

Adding a rule is a one-line edit to ``RULES``; the ``description`` is shown
verbatim to end users.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class RedFlag:
    id: str
    label: str
    description: str
    weight: int           # 1 (weak) .. 3 (near-decisive)
    behaviour: str        # behaviour bucket, e.g. "authority_impersonation"
    patterns: tuple[str, ...]
    _compiled: tuple[re.Pattern, ...] = field(default=(), compare=False, repr=False)

    def compiled(self) -> tuple[re.Pattern, ...]:
        if not self._compiled:
            object.__setattr__(
                self, "_compiled",
                tuple(re.compile(p, re.IGNORECASE) for p in self.patterns),
            )
        return self._compiled

    def search(self, text: str) -> str | None:
        for pat in self.compiled():
            m = pat.search(text)
            if m:
                return m.group(0)
        return None


@dataclass(frozen=True)
class FiredFlag:
    id: str
    label: str
    description: str
    weight: int
    behaviour: str
    match: str


RULES: tuple[RedFlag, ...] = (
    RedFlag(
        "digital_arrest", "'Digital arrest' / custody language",
        "Mentions a 'digital arrest', online custody or a warrant served over a "
        "call. 'Digital arrest' is not a real legal procedure — no agency arrests "
        "anyone over a video call.",
        3, "authority_impersonation",
        (r"\bdigital\s+arrest\b", r"\bonline\s+arrest\b", r"\barrest\s+warrant\b",
         r"\bnon[-\s]?bailable\b", r"\byou\s+are\s+under\s+(?:digital\s+)?arrest\b",
         r"\b(?:judicial\s+)?(?:remand|custody)\b",
         r"\bdigital\s+arrest\s+(?:mein|me|hain?|ho)\b", r"\bgiraftar?i?\b",
         r"डिजिटल\s*अरेस्ट", r"गिरफ्तार|गिरफ़्तार|गिरफ्तारी", r"हिरासत")),
    RedFlag(
        "authority_impersonation", "Authority impersonation",
        "Claims to be police, CBI, ED, RBI, customs, TRAI, narcotics or another "
        "agency. Real officials don't conduct investigations or demand money over "
        "WhatsApp/phone.",
        3, "authority_impersonation",
        (r"\b(?:CBI|RBI|TRAI)\b",
         r"\bED\b(?=.*\b(?:case|arrest|money\s+laundering|notice)\b)",
         r"\benforcement\s+directorate\b", r"\bcyber\s*crime\b", r"\bnarcotics?\b",
         r"\bcustoms?\s+(?:department|official|officer)\b",
         r"\bincome\s+tax\s+department\b",
         r"\b(?:police|inspector|sub[-\s]?inspector|constable|officer)\b",
         r"\bmumbai\s+police\b|\bdelhi\s+police\b|\bcyber\s+cell\b",
         r"पुलिस|सीबीआई|ईडी\b|साइबर\s*क्राइम|नार्कोटिक्स|कस्टम",
         r"\bthana\b|\bthane\s+se\b")),
    RedFlag(
        "money_demand", "Demand to transfer money",
        "Asks you to pay a fine, penalty, 'security deposit' or to move money to a "
        "'safe'/'RBI verification' account. No agency asks you to transfer money to "
        "prove innocence.",
        3, "money_request",
        (r"\bsafe\s+(?:custody\s+)?account\b", r"\bsecurity\s+deposit\b",
         r"\bverification\s+(?:fee|charge|deposit)\b", r"\bclearance\s+(?:fee|charge)\b",
         r"\bprove\s+your\s+innocence\b",
         r"\b(?:transfer|deposit|pay|remit|send)\b[^.]{0,40}\b(?:money|amount|funds?|rs\.?|inr|rupees?|₹|lakhs?|crores?)\b",
         r"\b(?:RTGS|NEFT|IMPS|UPI)\b", r"\bfine\s+of\b|\bpenalty\s+of\b",
         r"\bpaise?\s+(?:transfer|bhej|jama|de\s+do|deposit)",
         r"\b(?:transfer|jama)\s+kar(?:o|do|en|na|iye)?\b",
         r"\bsafe\s+account\s+(?:mein|me)\b",
         r"पैसे?\s*(?:ट्रांसफर|भेज|जमा)|ट्रांसफर\s*कर|रुपये\s*(?:भेज|जमा)",
         r"सुरक्षित\s*(?:खाते|अकाउंट)")),
    RedFlag(
        "credential_request", "Requests OTP / bank / ID details",
        "Asks for an OTP, CVV, PIN, full card/bank number, Aadhaar or PAN. "
        "Legitimate officials and banks never ask for these.",
        3, "credential_request",
        (r"\bOTP\b", r"\bone[-\s]?time\s+password\b", r"\bCVV\b",
         r"\b(?:ATM\s+)?PIN\b", r"\bcard\s+number\b",
         r"\b(?:bank\s+)?account\s+(?:number|details)\b",
         r"\bAadhaar\b|\bAadhar\b|\bPAN\s+(?:card|number)\b",
         r"\bOTP\s+(?:bhej|bata|share\s+kar|do)",
         r"ओटीपी|आधार\s*(?:नंबर|कार्ड)?|पैन\s*कार्ड",
         r"\bbank\s+detail(?:s)?\s+(?:bhej|do|bata)")),
    RedFlag(
        "secrecy_isolation", "Secrecy / stay-on-the-call pressure",
        "Tells you to keep it confidential, not tell family, or to stay on the "
        "call/video. Isolation is a core coercion tactic of this scam.",
        2, "secrecy",
        (r"\bdo\s+not\s+(?:tell|inform|disclose)\b", r"\bdon'?t\s+(?:tell|inform|disclose)\b",
         r"\bkeep\s+(?:this|it)\s+confidential\b", r"\bstay\s+on\s+the\s+(?:call|line)\b",
         r"\bdo\s+not\s+(?:disconnect|hang\s+up|cut\s+the\s+call)\b",
         r"\bremain\s+available\b", r"\bunder\s+(?:surveillance|investigation)\b",
         r"\bkisi\s+ko\s+(?:mat|na|nahi)\s+bata",
         r"\b(?:phone|call|line)\s+(?:band|disconnect|cut|kaat)\s*(?:mat|nahi)",
         r"\bcall\s+(?:pe|par)\s+(?:bane?\s+raho|raho)",
         r"किसी\s+को\s+(?:मत|नहीं)\s+बता", r"फ़?ोन\s+(?:बंद|काट)\s+मत|कॉल\s+मत\s+काट")),
    RedFlag(
        "urgency_threat", "Urgency / legal threat",
        "Creates extreme time pressure or threatens immediate arrest, FIR or "
        "account freeze. Pressure to act 'right now' stops you checking.",
        2, "urgency",
        (r"\bimmediately\b", r"\bwithin\s+\d+\s*(?:hours?|minutes?|hrs?|min)\b",
         r"\b(?:final|last)\s+(?:notice|warning)\b", r"\blegal\s+action\b",
         r"\bFIR\b|\bF\.?I\.?R\.?\b", r"\baccount\s+(?:will\s+be\s+)?(?:freez|block|suspend)",
         r"\bact\s+now\b|\burgent(?:ly)?\b",
         r"\bturant\b|\bjaldi\s+karo\b|\bwarna\b",
         r"तुरंत|अभी\s+करें|वरना|जल्दी\s+करो")),
    RedFlag(
        "threat", "Direct threat / intimidation",
        "Threatens arrest, jail, asset seizure or harm to coerce compliance.",
        2, "threat",
        (r"\bwill\s+be\s+arrested\b", r"\bgo\s+to\s+jail\b", r"\bseize\s+your\s+(?:assets|property|account)\b",
         r"\bblacklist", r"\bjail\s+ho\s+jayegi\b", r"जेल|गिरफ्तार\s+कर\s+लेंगे|जब्त")),
    RedFlag(
        "video_call_platform", "Move to WhatsApp / Skype video",
        "Pushes the conversation onto a WhatsApp/Skype video call to impersonate "
        "an officer in uniform / fake police station.",
        2, "video_call_pressure",
        (r"\bwhats\s*app\s+(?:video\s+)?call\b", r"\bskype\s+(?:video\s+)?call\b",
         r"\bjoin\s+(?:the\s+)?video\s+call\b",
         r"\bvideo\s+(?:call|conference)\b[^.]{0,30}\b(?:officer|police|interrogat)",
         r"\bvideo\s+call\s+(?:pe|par|join)", r"वीडियो\s*कॉल")),
    RedFlag(
        "parcel_hook", "Suspicious parcel / courier hook",
        "Opens with a 'parcel held by customs' containing drugs, fake passports or "
        "illegal items — a common entry point to the scam.",
        2, "fear",
        (r"\b(?:parcel|package|courier|consignment|shipment)\b",
         r"\bseized\s+(?:by\s+)?customs\b",
         r"\bcontains?\s+(?:drugs?|narcotics?|illegal|contraband|MDMA|passport)\b",
         r"पार्सल|कूरियर|कुरियर", r"\bparcel\s+(?:mein|me)\b.{0,30}(?:drugs?|MDMA)")),
    RedFlag(
        "emotional_pressure", "Emotional manipulation",
        "Uses fear, panic or false reassurance ('don't worry, just cooperate') to "
        "keep the victim compliant and isolated.",
        1, "emotional_manipulation",
        (r"\bdon'?t\s+(?:panic|worry)\b", r"\bcooperate\s+with\s+(?:us|me)\b",
         r"\btrust\s+me\b", r"\byour\s+family\s+(?:is\s+)?(?:in\s+danger|at\s+risk)\b",
         r"घबराओ\s+मत|सहयोग\s+करो")),
    RedFlag(
        "case_reference", "Fake case / reference number",
        "Quotes an official-sounding case, FIR or reference number to seem "
        "legitimate. Genuine notices arrive in writing, not over a call.",
        1, "authority_impersonation",
        (r"\bcase\s+(?:id|no\.?|number|ref)\b", r"\bcomplaint\s+(?:no\.?|number)\b",
         r"\breference\s+(?:no\.?|number|code)\b", r"\bDD[-\s]?\d{2,}\b")),
    RedFlag(
        "suspicious_link", "Suspicious link",
        "Contains a link to click. Scam links impersonate official portals to "
        "harvest details or push remote-access apps.",
        1, "urgency",
        (r"https?://\S+", r"\bwww\.\S+", r"\b(?:bit\.ly|tinyurl|t\.me|rb\.gy|cutt\.ly)/\S+")),
)

RULES_BY_ID = {r.id: r for r in RULES}
MAX_WEIGHT = sum(r.weight for r in RULES)


def scan(text: str, rules: Iterable[RedFlag] = RULES) -> list[FiredFlag]:
    """Return every rule that fires on ``text`` (in RULES order)."""
    if not text:
        return []
    fired: list[FiredFlag] = []
    for rule in rules:
        match = rule.search(text)
        if match is not None:
            fired.append(FiredFlag(rule.id, rule.label, rule.description,
                                   rule.weight, rule.behaviour, match.strip()[:120]))
    return fired


def rule_score(text: str) -> float:
    """Collapse fired flags into a saturating 0..1 risk score."""
    fired = scan(text)
    if not fired:
        return 0.0
    w = sum(f.weight for f in fired)
    return round(w / (w + 3.5), 4)
