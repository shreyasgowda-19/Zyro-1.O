import re
from typing import Dict, Any, List
from app.services.credential_guard import validate_sensitive_input

# Regex patterns for deterministic scan
URGENCY_PATTERNS = [
    r"\burgent\b", r"\bimmediately\b", r"\bwithin 24 hours?\b",
    r"\baccount suspended\b", r"\belectricity (?:will be )?disconnected\b",
    r"\bpower disconnect(?:ed)?\b", r"\bsim (?:will be )?block(?:ed)?\b",
    r"\bservice deactivated\b", r"\bact now\b", r"\baction required\b",
    r"\blegal notice\b", r"\barrest warrant\b", r"\bpolice case\b",
    r"\bfinal warning\b", r"\blast reminder\b", r"\bblocked today\b"
]

KYC_PATTERNS = [
    r"\bkyc update\b", r"\bupdate kyc\b", r"\bverify pan\b",
    r"\bupdate pan\b", r"\bverify aadhaar\b", r"\blink aadhaar\b",
    r"\bunblock account\b", r"\bsubmit documents\b", r"\breactivate account\b",
    r"\bverify (?:your )?bank\b", r"\bcomplete kyc\b", r"\bkyc expired\b"
]

FINANCIAL_LURE_PATTERNS = [
    r"\blottery\b", r"\bcashback\b", r"\bwon prize\b", r"\bwon cash\b",
    r"\bwon a car\b", r"\bclaim bonus\b", r"\bpart-?time job\b",
    r"\bdaily income\b", r"\btask earning\b", r"\bwork from home\b",
    r"\blakhs? won\b", r"\bcrores? won\b", r"\bcongratulations you won\b"
]

SHORTENED_URL_PATTERN = re.compile(
    r"\b(?:https?://)?(?:bit\.ly|tinyurl\.com|is\.gd|t\.co|cutt\.ly|rb\.gy|shorturl\.at|tiny\.cc|ow\.ly|buff\.ly|goo\.gl)/[a-zA-Z0-9_\-]+",
    re.IGNORECASE
)

INSECURE_HTTP_PATTERN = re.compile(
    r"\bhttp://[a-zA-Z0-9.\-]+",
    re.IGNORECASE
)

IP_URL_PATTERN = re.compile(
    r"\bhttps?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    re.IGNORECASE
)

REMOTE_ACCESS_PATTERNS = [
    r"\banydesk\b", r"\bteamviewer\b", r"\brustdesk\b",
    r"\bquicksupport\b", r"\bscreen share\b"
]

COLLECT_TRAP_PATTERNS = [
    r"\bapprove (?:request )?to receive\b",
    r"\bscan qr to receive\b",
    r"\benter pin to (?:get|receive)\b",
    r"\benter upi pin to receive\b",
    r"\breceive refund.*enter pin\b"
]

def check_message_for_scam(message: str) -> Dict[str, Any]:
    """
    Deterministic scam message heuristic scanner.
    First runs text through credential guard.
    NEVER logs or stores the input message.
    """
    # 1. Credential guard validation (§11, §14)
    # Rejects standalone credentials, card numbers, or keyword near digits
    norm_text = validate_sensitive_input(message, field_name="message")

    text_lower = norm_text.lower()
    matched_signals = []

    # Check Urgency
    if any(re.search(p, text_lower) for p in URGENCY_PATTERNS):
        matched_signals.append({
            "code": "urgency_threat",
            "name": "Urgency & Threat Pressure",
            "description": "Message creates panic, fear of service disconnection, or artificial urgency."
        })

    # Check KYC / Account Phishing
    if any(re.search(p, text_lower) for p in KYC_PATTERNS):
        matched_signals.append({
            "code": "kyc_phishing",
            "name": "KYC / Account Verification Bait",
            "description": "Message prompts for sensitive document submission, KYC completion, or unblocking."
        })

    # Check Financial Lure
    if any(re.search(p, text_lower) for p in FINANCIAL_LURE_PATTERNS):
        matched_signals.append({
            "code": "financial_lure",
            "name": "Prize / Lottery / Quick Money Lure",
            "description": "Message promises unverified rewards, lottery winnings, or lucrative remote jobs."
        })

    # Check Suspicious Links
    has_short_link = bool(SHORTENED_URL_PATTERN.search(text_lower))
    has_http_link = bool(INSECURE_HTTP_PATTERN.search(text_lower))
    has_ip_link = bool(IP_URL_PATTERN.search(text_lower))

    if has_short_link or has_http_link or has_ip_link:
        details = []
        if has_short_link:
            details.append("masked/shortened link")
        if has_http_link:
            details.append("insecure non-HTTPS link")
        if has_ip_link:
            details.append("direct IP address link")
        matched_signals.append({
            "code": "suspicious_link",
            "name": "Suspicious or Masked Web Link",
            "description": f"Contains potentially deceptive URL: {', '.join(details)}."
        })

    # Check Remote Access Tool
    if any(re.search(p, text_lower) for p in REMOTE_ACCESS_PATTERNS):
        matched_signals.append({
            "code": "remote_access",
            "name": "Remote Access Tool Request",
            "description": "Requests installing remote desktop screen-sharing tools (AnyDesk, TeamViewer, etc.)."
        })

    # Check Collect Request / QR Trap
    if any(re.search(p, text_lower) for p in COLLECT_TRAP_PATTERNS):
        matched_signals.append({
            "code": "collect_trap",
            "name": "Collect Request / QR Code Trap",
            "description": "Claims you must scan a QR code or enter a PIN to receive incoming money or refunds."
        })

    num_signals = len(matched_signals)
    has_severe = any(s["code"] in ("remote_access", "collect_trap") for s in matched_signals)

    if num_signals == 0:
        risk_level = "low"
        is_suspicious = False
        advice_codes = [
            "scam_advice.stay_vigilant",
            "scam_advice.official_channels"
        ]
    elif num_signals == 1 and not has_severe:
        risk_level = "medium"
        is_suspicious = True
        advice_codes = [
            "scam_advice.verify_source",
            "scam_advice.never_share_credentials"
        ]
    else:
        risk_level = "high"
        is_suspicious = True
        advice_codes = [
            "scam_advice.do_not_click",
            "scam_advice.do_not_pay",
            "scam_advice.never_share_credentials",
            "scam_advice.report_1930"
        ]

    return {
        "is_suspicious": is_suspicious,
        "risk_level": risk_level,
        "matched_signals": matched_signals,
        "advice_codes": advice_codes,
        "disclaimer": "Heuristic check, not a verdict. Never share OTP or PIN."
    }
