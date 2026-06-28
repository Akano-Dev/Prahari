// Labelled demo call scripts for the live simulator. These are *defensive*
// examples — modelled on documented scam tactics so the detector can be shown
// working — plus a legit call that must NOT false-positive. No real calls are
// ever placed; every line is streamed through the real backend pipeline.

export interface Scenario {
  id: string;
  label: string;
  caller: string;
  tag: string;
  language: "English" | "Hinglish" | "Hindi";
  scam: boolean;       // expected outcome (for the picker badge)
  lines: string[];
}

export const SCENARIOS: Scenario[] = [
  {
    id: "digital_arrest",
    label: "Digital arrest (CBI)",
    caller: "+91 98XXXXXX21",
    tag: "Digital arrest",
    language: "English",
    scam: true,
    lines: [
      "Hello, this is Inspector Sharma from the CBI Cyber Crime branch.",
      "A parcel in your name was seized by customs and it contains MDMA.",
      "You are now under digital arrest. Do not disconnect this call and do not tell anyone.",
      "Stay on the WhatsApp video call so we can verify your identity.",
      "Transfer Rs 50,000 to the RBI safe account immediately and share the OTP to verify.",
    ],
  },
  {
    id: "bank_kyc",
    label: "Bank KYC block",
    caller: "+91 80XXXXXX09",
    tag: "KYC / account fraud",
    language: "English",
    scam: true,
    lines: [
      "Good afternoon, I am calling from your bank's security department.",
      "Your account will be blocked today because your KYC has expired.",
      "To re-verify, please tell me the OTP we just sent to your phone.",
      "Also confirm your debit card number and the CVV on the back.",
      "If you do not verify in 10 minutes your account will be frozen permanently.",
    ],
  },
  {
    id: "lottery",
    label: "Lottery / prize",
    caller: "+91 70XXXXXX55",
    tag: "Lottery scam",
    language: "English",
    scam: true,
    lines: [
      "Congratulations! Your number has won the KBC lucky draw of Rs 25 lakh.",
      "To release your prize you must pay a small refundable processing fee.",
      "Send Rs 8,500 as GST charges to this account and keep it confidential.",
      "Do not tell anyone or you will lose the prize money.",
    ],
  },
  {
    id: "tech_refund",
    label: "Tech-support refund",
    caller: "+1 8XX-XXX-4417",
    tag: "Tech support",
    language: "English",
    scam: true,
    lines: [
      "Hello, I'm calling from Microsoft technical support about your computer.",
      "We detected a virus and we owe you a refund for your expired subscription.",
      "Please install AnyDesk so I can connect and process your refund.",
      "Now open your banking app and share the OTP so I can credit the money.",
    ],
  },
  {
    id: "digital_arrest_hinglish",
    label: "Digital arrest (Hinglish)",
    caller: "+91 99XXXXXX87",
    tag: "Digital arrest",
    language: "Hinglish",
    scam: true,
    lines: [
      "Namaste, main Mumbai cyber police se bol raha hoon.",
      "Aapke naam ka ek parcel pakda gaya hai jisme illegal items hain.",
      "Aap abhi digital arrest mein hain, call disconnect mat kijiye.",
      "Safe account mein paise transfer karo aur OTP bhejo, warna giraftari ho jayegi.",
    ],
  },
  {
    id: "legit_delivery",
    label: "Legit delivery (safe)",
    caller: "+91 91XXXXXX30",
    tag: "Genuine call",
    language: "English",
    scam: false,
    lines: [
      "Hi, this is Ravi from BlueDart, I have a parcel for delivery.",
      "I'm near your gate but can't find the flat number.",
      "Could you share the building name? I'll be there in five minutes.",
      "Great, thank you. See you shortly.",
    ],
  },
];

export const DEFAULT_SCENARIO = SCENARIOS[0];
