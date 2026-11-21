import re
import unicodedata
from typing import Tuple, Optional
from app.errors import AppError

DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

CREDENTIAL_KEYWORDS = [
    r"\botp\b", r"\bpin\b", r"\bcvv\b", r"\bcvc\b",
    r"\bpassword\b", r"\bpasscode\b", r"\bone\s+time\s+password\b"
]

# Allowed characters: Unicode letters, digits, spaces, and safe punctuation: . , - _ / : ( ) ₹ & ' ! ? %
SAFE_TEXT_PATTERN = re.compile(r"^[\w\s.,\-_/:()₹&'!?%]+$", re.UNICODE)
DANGEROUS_PATTERNS = [
    re.compile(r"<"),
    re.compile(r">"),
    re.compile(r"`"),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")  # Control characters
]

def normalize_text(text: str) -> str:
    """Normalize text: Unicode NFKC, strip zero-width characters, map Devanagari digits to ASCII."""
    if not text:
        return ""
    # Unicode NFKC
    nfkc = unicodedata.normalize("NFKC", text)
    # Strip zero-width characters (\u200B, \u200C, \u200D, \uFEFF)
    zero_width = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", nfkc)
    # Map Devanagari digits
    result = []
    for ch in zero_width:
        result.append(DEVANAGARI_DIGITS.get(ch, ch))
    return "".join(result)

def luhn_checksum(card_number_str: str) -> bool:
    """Validate 13-19 digit sequence with Luhn algorithm."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0

def validate_sensitive_input(text: Optional[str], field_name: str = "text") -> str:
    """
    Validates free-text fields per §11:
    - Checks for script text / control chars -> INVALID_TEXT
    - Checks for credentials (keyword near 3-8 digits, 4-8 digit standalone number, Luhn card sequence) -> CREDENTIAL_INPUT_REJECTED
    - Returns normalized text if valid
    - NEVER echoes or logs rejected value
    """
    if not text:
        return ""

    # 1. Normalize
    norm = normalize_text(text).strip()
    if not norm:
        return ""

    # 2. Check for script injection / dangerous characters
    for dang in DANGEROUS_PATTERNS:
        if dang.search(norm):
            raise AppError(
                code="INVALID_TEXT",
                message=f"Field '{field_name}' contains invalid or prohibited characters.",
                status_code=422,
                params={"field": field_name}
            )

    if not SAFE_TEXT_PATTERN.match(norm):
        raise AppError(
            code="INVALID_TEXT",
            message=f"Field '{field_name}' contains characters outside the allowed set.",
            status_code=422,
            params={"field": field_name}
        )

    # 3. Check for standalone 4–8 digit number
    if re.fullmatch(r"\d{4,8}", norm):
        raise AppError(
            code="CREDENTIAL_INPUT_REJECTED",
            message=f"Security alert: Field '{field_name}' appears to contain a standalone security credential.",
            status_code=422,
            params={"field": field_name, "rule": "standalone_pin_otp"}
        )

    # 4. Check for Luhn 13–19 digit sequence (allowing spaces and hyphens)
    card_candidates = re.findall(r"(?:\d[ -]*?){13,19}", norm)
    for cand in card_candidates:
        clean_cand = re.sub(r"[ -]", "", cand)
        if 13 <= len(clean_cand) <= 19 and luhn_checksum(clean_cand):
            raise AppError(
                code="CREDENTIAL_INPUT_REJECTED",
                message=f"Security alert: Field '{field_name}' appears to contain a payment card number.",
                status_code=422,
                params={"field": field_name, "rule": "luhn_card_number"}
            )

    # 5. Check for credential keyword within 25 characters of a 3–8 digit number
    # Special near-miss check: 'pin code 560001' or 'pincode 560001' is a standard Indian postal code
    norm_lower = norm.lower()
    
    # Check each keyword
    for kw_pattern in CREDENTIAL_KEYWORDS:
        for match in re.finditer(kw_pattern, norm_lower):
            kw_start = match.start()
            kw_end = match.end()

            # Check if this keyword is part of 'pin code' or 'pincode'
            # Lookahead / behind for 'code'
            following_text = norm_lower[kw_end:kw_end+10].strip()
            if match.group().strip() == "pin" and following_text.startswith("code"):
                continue  # 'pin code' is legitimate postal code address

            # Look within 25 chars before and after
            start_window = max(0, kw_start - 25)
            end_window = min(len(norm_lower), kw_end + 25)
            window = norm[start_window:end_window]

            # Find 3-8 digit number in window
            if re.search(r"\b\d{3,8}\b", window):
                raise AppError(
                    code="CREDENTIAL_INPUT_REJECTED",
                    message=f"Security alert: Field '{field_name}' appears to contain a security PIN or OTP credential.",
                    status_code=422,
                    params={"field": field_name, "rule": "keyword_near_digits"}
                )

    return norm
