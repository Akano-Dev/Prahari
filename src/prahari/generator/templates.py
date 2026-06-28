"""Synthetic, labelled example generator (DEFENSIVE use only).

Why this exists
---------------
The public Kaggle corpora (SMS spam, fraud/phishing email) under-represent the
specific Indian "digital arrest" scam Prahari targets. To teach and *test* the
detector we synthesise labelled examples by slot-filling templates:

* ``scam``  — realistic digital-arrest scripts (authority + custody + money +
  secrecy), built from interchangeable fragments so the model learns the
  *pattern*, not one fixed string.
* ``legit`` — benign look-alikes: real delivery updates, OTP receipts, personal
  chats and genuine bank alerts, including some that share surface words
  ("account", "OTP", "police") so the model can't cheat on keywords alone.

This generator is **not** a tool for deceiving anyone. Its only outputs are
labelled rows used to train and test a defensive classifier, mirroring scams
already documented publicly by police cyber-crime advisories.

Two entry points share the same machinery:

* :func:`generate` — used by the Phase-3 ``augment`` command (source tag
  ``"synthetic"``).
* fixtures (Phase 6) call :func:`generate` with a *different* seed so test data
  never overlaps the training augmentation.
"""
from __future__ import annotations

import random
from typing import Optional

import pandas as pd

from prahari import config

# --------------------------------------------------------------------------- #
# Slot vocabularies
# --------------------------------------------------------------------------- #
_AGENCIES = [
    "CBI", "the Enforcement Directorate", "the Cyber Crime Branch",
    "Mumbai Police", "the Narcotics Control Bureau", "the Customs Department",
    "TRAI", "Delhi Police Cyber Cell", "the Income Tax Department",
]
_OFFICERS = [
    "Inspector Sharma", "ASI Verma", "Officer Rajesh Kumar", "DCP Mehta",
    "Sub-Inspector Singh", "Officer Priya Nair",
]
_AMOUNTS = [
    "Rs 25,000", "Rs 50,000", "Rs 1,20,000", "₹2,50,000", "Rs 75,000",
    "Rs 3 lakh", "₹90,000",
]
_DEADLINES = [
    "within 2 hours", "within 30 minutes", "immediately", "before 5 PM today",
    "within the next hour", "right now",
]
_PLATFORMS = ["WhatsApp video call", "Skype call", "WhatsApp", "a video call"]
_PAY = ["RTGS", "NEFT", "a UPI transfer", "IMPS"]
_CONTRABAND = ["MDMA drugs", "16 fake passports", "illegal SIM cards",
               "narcotics", "a fake passport and credit cards"]
_CASES = ["FIR No. DD-4471/2024", "case ID CYB-90213", "complaint no. 88231",
          "reference code RBI-5589"]
_COURIERS = ["FedEx", "DHL", "BlueDart", "the customs department"]
# Real couriers for the *legit* delivery template (no agency look-alikes).
_LEGIT_COURIERS = ["BlueDart", "Delhivery", "India Post", "Amazon", "Ekart"]

# --------------------------------------------------------------------------- #
# Templates. {slots} are filled from the vocabularies above.
# --------------------------------------------------------------------------- #
_SCAM_TEMPLATES = [
    "This is {officer} from {agency}. A parcel in your name has been seized by "
    "{courier} and it contains {contraband}. You are now under digital arrest. "
    "Do not disconnect this call. Transfer {amount} to the RBI safe-custody "
    "account {deadline} to prove your innocence, and share the OTP to verify.",

    "ATTENTION: {agency} has registered {case} against your Aadhaar. You are "
    "under digital arrest and must stay on the {platform} until cleared. Pay a "
    "verification deposit of {amount} via {pay} {deadline} or a non-bailable "
    "arrest warrant will be issued. Do not tell anyone about this case.",

    "{officer} speaking, {agency}. Your bank account is linked to money "
    "laundering. Join the {platform} now and keep it confidential. To avoid "
    "immediate arrest, move {amount} to the secure government account {deadline}. "
    "Share your account number, CVV and the OTP for verification.",

    "URGENT NOTICE from {agency}. {case} filed against you for an illegal "
    "parcel containing {contraband}. This is a digital arrest. Settle the "
    "clearance fee of {amount} {deadline} through {pay}. Stay on the call and "
    "do not inform your family or it will be treated as obstruction.",

    "Dear customer, your number will be disconnected by {agency} {deadline}. "
    "Your Aadhaar is misused in a criminal case. Press 1 to connect to {officer} "
    "on a {platform}. You are under investigation; pay {amount} security deposit "
    "to lift the digital arrest and remain available on the line.",

    # --- Hinglish (romanized Hindi) — the most common real-world phrasing. ---
    "{officer} bol raha hoon {agency} se. Aapke naam ka parcel {courier} ne "
    "seize kiya hai jisme {contraband} mila hai. Aap ab digital arrest mein "
    "hain. Phone band mat karo aur kisi ko mat batao. {amount} RBI safe account "
    "mein {deadline} transfer karo aur OTP bhejo, warna giraftari ho jayegi.",

    "Namaste, {agency} se baat kar rahe hain. {case} aapke khilaaf darj hua hai. "
    "Aap digital arrest mein hain, {platform} pe bane raho. {amount} verification "
    "ke liye {pay} se {deadline} jama karo warna non-bailable warrant nikal "
    "jayega. Yeh baat kisi ko mat batana.",

    # --- Devanagari (Hindi script). ---
    "{agency} की ओर से सूचना: {case} आपके खिलाफ दर्ज है। आप डिजिटल अरेस्ट में "
    "हैं और {platform} पर बने रहें। किसी को मत बताएं। {amount} सुरक्षित खाते में "
    "तुरंत ट्रांसफर करें वरना गिरफ्तारी होगी। सत्यापन के लिए ओटीपी भेजें।",
]

# Benign messages. Some deliberately share surface words with scams.
_LEGIT_TEMPLATES = [
    "Hi {name}, running a bit late for dinner. Should reach the restaurant by "
    "8:30. Order the starters if you're hungry!",

    "Your {legit_courier} parcel with tracking ID {track} is out for delivery "
    "today and will arrive between 2 PM and 6 PM. Reply STOP to opt out.",

    "{bank}: Rs {small} debited from a/c XX{acct} on 12-06 to UPI. Not you? "
    "Call our official number on the back of your card. We never ask for OTP.",

    "Your OTP for logging into {bank} NetBanking is {otp}. Valid for 10 minutes. "
    "Do not share it with anyone, including bank staff.",

    "Reminder: your appointment with Dr. {name} is tomorrow at 11 AM. Please "
    "arrive 10 minutes early and bring your previous reports.",

    "Team, the project sync is moved to 4 PM today. I've updated the calendar "
    "invite. Ping me if that clashes with anything.",

    "Congratulations {name}! Your electricity bill of Rs {small} is paid. "
    "Thank you for using the official BESCOM portal.",

    "Police helpline community update: a road safety drive is on near MG Road "
    "this weekend. Drive safe and wear seatbelts.",

    "Mom, I reached the hostel safely. Network was bad on the train. Will video "
    "call you tonight after dinner. Love you.",

    "Your food order from Spice Garden has been confirmed and will be delivered "
    "in 35 minutes. Track it in the app.",

    # --- Benign Hinglish / Devanagari look-alikes (share surface words). ---
    "Maa, main hostel safely pahunch gaya. Train mein network nahi tha. Aaj "
    "raat khaane ke baad video call karunga. Apna khayal rakhna, love you.",

    "Aapka {legit_courier} parcel tracking ID {track} aaj shaam tak deliver ho "
    "jayega. Order ke baare mein koi sawaal ho to app par track karein.",

    "{bank} OTP {otp} hai, NetBanking login ke liye. Yeh OTP kisi ko mat batayein, "
    "bank staff bhi kabhi OTP nahi maangta.",

    "नमस्ते {name}, कल 11 बजे डॉक्टर का अपॉइंटमेंट है। कृपया 10 मिनट पहले पहुँचें "
    "और अपनी पुरानी रिपोर्ट साथ लाएँ।",
]

_NAMES = ["Anita", "Rohan", "Priya", "Vikram", "Sneha", "Arjun", "Kavya"]
_BANKS = ["HDFC Bank", "SBI", "ICICI Bank", "Axis Bank"]


def _fill(template: str, rng: random.Random) -> str:
    return template.format(
        officer=rng.choice(_OFFICERS),
        agency=rng.choice(_AGENCIES),
        amount=rng.choice(_AMOUNTS),
        deadline=rng.choice(_DEADLINES),
        platform=rng.choice(_PLATFORMS),
        pay=rng.choice(_PAY),
        contraband=rng.choice(_CONTRABAND),
        case=rng.choice(_CASES),
        courier=rng.choice(_COURIERS),
        legit_courier=rng.choice(_LEGIT_COURIERS),
        name=rng.choice(_NAMES),
        bank=rng.choice(_BANKS),
        track=f"{rng.randint(100000, 999999)}",
        small=f"{rng.choice([299, 540, 1299, 2350, 760])}",
        acct=f"{rng.randint(1000, 9999)}",
        otp=f"{rng.randint(100000, 999999)}",
    )


def _generate_class(
    templates: list[str], label: str, n: int, rng: random.Random
) -> list[dict]:
    rows = []
    seen: set[str] = set()
    attempts = 0
    # Oversample then de-dup so we return ~n distinct strings.
    while len(rows) < n and attempts < n * 20:
        attempts += 1
        text = _fill(rng.choice(templates), rng)
        if text in seen:
            continue
        seen.add(text)
        rows.append({"text": text, "label": label, "source": "synthetic"})
    return rows


def generate(
    n_scam: int = 400,
    n_legit: int = 400,
    seed: int = config.RANDOM_SEED,
) -> pd.DataFrame:
    """Return a shuffled DataFrame of synthetic ``[text, label, source]`` rows.

    Parameters
    ----------
    n_scam, n_legit : int
        Target number of distinct scam / legit examples.
    seed : int
        RNG seed. Use a *different* seed for test fixtures than for training
        augmentation so the two never overlap.
    """
    rng = random.Random(seed)
    rows = (
        _generate_class(_SCAM_TEMPLATES, config.LABEL_SCAM, n_scam, rng)
        + _generate_class(_LEGIT_TEMPLATES, config.LABEL_LEGIT, n_legit, rng)
    )
    rng.shuffle(rows)
    return pd.DataFrame(rows, columns=["text", "label", "source"])
