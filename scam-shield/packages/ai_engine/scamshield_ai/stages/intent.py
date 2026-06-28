"""Stage 3 — intent detection (heuristic).

Tags the *speech act* of an utterance — what the caller is trying to get the
victim to do — independent of scam category. These intents feed the behaviour
read and the LLM reasoning prompt. Swappable for a fine-tuned classifier.
"""
from __future__ import annotations

import re

from ..context import ConversationState

_INTENTS: list[tuple[str, re.Pattern]] = [
    ("demand_payment", re.compile(r"\b(transfer|deposit|pay|remit|send)\b.*\b(money|amount|rs|inr|rupees|₹|account)\b|"
                                  r"\bpaise?\s+(?:transfer|bhej|jama)\b|ट्रांसफर\s*कर", re.IGNORECASE)),
    ("request_credentials", re.compile(r"\b(otp|cvv|pin|password|card\s+number|account\s+number|aadhaar|pan)\b|"
                                       r"ओटीपी|आधार", re.IGNORECASE)),
    ("threaten", re.compile(r"\b(arrest|jail|fir|legal\s+action|seize|freeze|warrant)\b|"
                            r"गिरफ्तार|जेल|वरना", re.IGNORECASE)),
    ("impose_authority", re.compile(r"\b(cbi|rbi|police|enforcement|customs|officer|inspector)\b|"
                                    r"सीबीआई|पुलिस", re.IGNORECASE)),
    ("create_urgency", re.compile(r"\b(immediately|now|within\s+\d+|urgent|right\s+now)\b|तुरंत|अभी", re.IGNORECASE)),
    ("isolate", re.compile(r"\b(do\s+not\s+tell|don'?t\s+tell|confidential|stay\s+on\s+the\s+(?:call|line))\b|"
                           r"किसी\s+को\s+मत|kisi\s+ko\s+mat", re.IGNORECASE)),
    ("move_platform", re.compile(r"\b(whatsapp|skype|video\s+call)\b|वीडियो\s*कॉल", re.IGNORECASE)),
    ("install_software", re.compile(r"\b(anydesk|teamviewer|remote\s+access|install\s+the\s+app)\b", re.IGNORECASE)),
]


class IntentStage:
    name = "intent"

    def process(self, utterance: str, state: ConversationState) -> None:
        for intent, pat in _INTENTS:
            if pat.search(utterance):
                if intent not in state.intents:
                    state.intents.add(intent)
                    state.add_timeline("note", f"intent: {intent}")
