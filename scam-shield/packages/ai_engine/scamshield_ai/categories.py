"""Scam-category registry — the system's extensibility point.

Each category is one :class:`ScamCategory` entry: a stable id, a human label, a
weight, and keyword/regex matchers (English + Hindi/Hinglish). The
``pattern_matching`` stage scores every category against the conversation and
surfaces the strongest. **Adding a scam type is a single entry here** — nothing
else in the pipeline changes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScamCategory:
    id: str
    label: str
    weight: float                 # base severity 0..1 when strongly matched
    patterns: tuple[str, ...]
    _compiled: tuple[re.Pattern, ...] = field(default=(), compare=False, repr=False)

    def compiled(self) -> tuple[re.Pattern, ...]:
        if not self._compiled:
            object.__setattr__(
                self, "_compiled",
                tuple(re.compile(p, re.IGNORECASE) for p in self.patterns),
            )
        return self._compiled

    def match_strength(self, text: str) -> float:
        """Fraction of this category's patterns present in ``text`` (0..1)."""
        if not text:
            return 0.0
        hits = sum(1 for pat in self.compiled() if pat.search(text))
        return hits / len(self.patterns) if self.patterns else 0.0


# The 20 required categories. Patterns are intentionally lightweight in this
# scaffold; deepen them per category as real data arrives.
CATEGORIES: tuple[ScamCategory, ...] = (
    ScamCategory("digital_arrest", "Digital Arrest", 1.0,
                 (r"digital\s+arrest", r"online\s+arrest", r"डिजिटल\s*अरेस्ट",
                  r"\bgiraftar?i?\b", r"under\s+arrest", r"custody")),
    ScamCategory("parcel_scam", "Parcel Scam", 0.9,
                 (r"parcel", r"courier|consignment|shipment", r"पार्सल|कूरियर",
                  r"seized\s+by\s+customs", r"contains?\s+(?:drugs|MDMA|passport)")),
    ScamCategory("fake_police", "Fake Police", 0.95,
                 (r"\bpolice\b", r"inspector|constable|sub[-\s]?inspector",
                  r"पुलिस|थाने\s+से", r"cyber\s+cell")),
    ScamCategory("fake_cbi", "Fake CBI", 0.95,
                 (r"\bCBI\b", r"central\s+bureau", r"सीबीआई")),
    ScamCategory("fake_ed", "Fake ED", 0.95,
                 (r"\bED\b", r"enforcement\s+directorate", r"money\s+laundering",
                  r"ईडी|मनी\s+लॉन्ड्रिंग")),
    ScamCategory("fake_rbi", "Fake RBI", 0.9,
                 (r"\bRBI\b", r"reserve\s+bank", r"आरबीआई", r"rbi\s+guidelines")),
    ScamCategory("kyc_scam", "KYC Scam", 0.85,
                 (r"\bKYC\b", r"re[-\s]?kyc", r"update\s+your\s+kyc",
                  r"केवाईसी", r"account\s+(?:will\s+be\s+)?suspend")),
    ScamCategory("bank_scam", "Bank Scam", 0.8,
                 (r"\bbank\b.*(?:verify|block|suspend)", r"account\s+(?:blocked|frozen)",
                  r"बैंक\s+खाता", r"debit\s+card\s+(?:blocked|expired)")),
    ScamCategory("investment_scam", "Investment Scam", 0.8,
                 (r"guaranteed\s+returns?", r"double\s+your\s+money", r"high\s+returns?",
                  r"निवेश", r"investment\s+(?:opportunity|plan)")),
    ScamCategory("crypto_scam", "Crypto Scam", 0.8,
                 (r"crypto|bitcoin|usdt|ethereum", r"binance|wallet\s+address",
                  r"क्रिप्टो", r"trading\s+platform")),
    ScamCategory("loan_scam", "Loan Scam", 0.75,
                 (r"instant\s+loan", r"pre[-\s]?approved\s+loan", r"processing\s+fee",
                  r"लोन|कर्ज", r"loan\s+approved")),
    ScamCategory("job_scam", "Job Scam", 0.75,
                 (r"work\s+from\s+home", r"part[-\s]?time\s+job", r"registration\s+fee",
                  r"नौकरी", r"earn\s+\d+\s+per\s+day")),
    ScamCategory("tech_support_scam", "Tech Support Scam", 0.8,
                 (r"tech(?:nical)?\s+support", r"anydesk|teamviewer|remote\s+access",
                  r"your\s+(?:computer|device)\s+(?:is\s+)?(?:infected|hacked)",
                  r"microsoft\s+support")),
    ScamCategory("sim_swap", "SIM Swap", 0.85,
                 (r"sim\s+(?:swap|card\s+(?:block|upgrade))", r"sim\s+will\s+be\s+(?:blocked|deactivated)",
                  r"\bTRAI\b", r"सिम\s+(?:कार्ड|ब्लॉक)")),
    ScamCategory("upi_scam", "UPI Scam", 0.85,
                 (r"\bUPI\b", r"collect\s+request", r"google\s+pay|phonepe|paytm",
                  r"यूपीआई", r"approve\s+(?:the\s+)?request")),
    ScamCategory("qr_scam", "QR Scam", 0.8,
                 (r"\bQR\s+code\b", r"scan\s+(?:this\s+)?qr", r"क्यूआर")),
    ScamCategory("lottery_scam", "Lottery Scam", 0.8,
                 (r"lottery|lucky\s+draw|you\s+have\s+won", r"prize\s+money",
                  r"लॉटरी|इनाम", r"kbc|kaun\s+banega")),
    ScamCategory("sextortion", "Sextortion", 0.95,
                 (r"sextortion", r"nude|naked|intimate\s+(?:photo|video)",
                  r"video\s+will\s+be\s+(?:leaked|viral)", r"screen\s+record")),
    ScamCategory("courier_scam", "Courier Scam", 0.8,
                 (r"\b(?:fedex|dhl|bluedart|dtdc)\b", r"delivery\s+failed",
                  r"customs\s+(?:duty|charge|clearance)")),
    ScamCategory("identity_theft", "Identity Theft", 0.8,
                 (r"aadhaar|aadhar|pan\s+card", r"identity\s+(?:theft|misuse)",
                  r"आधार\s+(?:कार्ड|नंबर)", r"your\s+(?:identity|documents)\s+(?:misused|stolen)")),
)

CATEGORIES_BY_ID = {c.id: c for c in CATEGORIES}


def register_category(category: ScamCategory) -> None:
    """Extend the registry at runtime (e.g. from a config file)."""
    global CATEGORIES
    if category.id in CATEGORIES_BY_ID:
        raise ValueError(f"category '{category.id}' already registered")
    CATEGORIES = CATEGORIES + (category,)
    CATEGORIES_BY_ID[category.id] = category
