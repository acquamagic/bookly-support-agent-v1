"""
PII / PCI guardrails for the Bookly support agent.

Detects sensitive data in user input before the agent processes it.
If a match is found the agent returns a safe refusal and the message
is never passed to slot-filling, intent routing, or tool calls.

Detected patterns
-----------------
PCI
  - Payment card numbers  (13–19 digits, spaced / dashed / continuous)
  - CVV / CVC codes       (3–4 digits near a CVV keyword)
  - Card expiry dates     (MM/YY or MM/YYYY near an expiry keyword)

PII
  - US Social Security Numbers  (XXX-XX-XXXX)
  - US phone numbers            (many common formats)
  - Passwords                   (value following a "password" keyword)
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# PCI — payment card number: 13–19 digits with optional spaces or dashes
# Uses a lookahead/lookbehind to avoid matching plain integers like order IDs.
_CARD_RE = re.compile(
    r"(?<!\d)"                        # not preceded by a digit
    r"(?:\d[ -]?){12,18}\d"          # 13–19 digits, optional separators
    r"(?!\d)",                        # not followed by a digit
)

# PCI — CVV/CVC: 3–4 digits near a keyword (allow "is" or ":" between keyword and digits)
_CVV_RE = re.compile(
    r"\b(?:cvv|cvc|cvv2|cid|security\s+code)(?:\s+is|\s*[:\s])\s*\d{3,4}\b",
    re.IGNORECASE,
)

# PCI — expiry date near a keyword
_EXPIRY_RE = re.compile(
    r"\b(?:expir(?:y|es?|ation)|exp\.?|valid\s+(?:thru|through|until))"
    r"[:\s]*(?:0[1-9]|1[0-2])\s*[/\-]\s*(?:\d{2}|\d{4})\b",
    re.IGNORECASE,
)

# PII — US Social Security Number
_SSN_RE = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[-\s](?!00)\d{2}[-\s](?!0000)\d{4}\b"
)

# PII — US phone numbers (many formats, including (area) code with parens)
_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?1[\s.\-]?)?"
    r"(?:\(\d{3}\)[\s.\-]?|\d{3}[\s.\-])"
    r"\d{3}[\s.\-]\d{4}\b"
)

# PII — password value following a keyword (catches "my password is abc123", "passcode: abc123")
_PASSWORD_RE = re.compile(
    r"\b(?:password|passwd|passcode)[\s:=]+(?:is\s+)?\S+",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Luhn check — reduces false positives on card number detection
# ---------------------------------------------------------------------------

def _luhn(digits: str) -> bool:
    """Return True if the digit string passes the Luhn algorithm."""
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class GuardrailHit:
    category: str   # "PCI" or "PII"
    kind: str       # e.g. "card_number", "ssn", "phone"
    redacted: str   # original text with sensitive part replaced by ***


def check(text: str) -> list[GuardrailHit]:
    """
    Scan *text* for PII/PCI patterns.
    Returns a list of GuardrailHit — empty list means input is clean.
    """
    hits: list[GuardrailHit] = []

    # --- PCI: card number (Luhn-validated) ---
    for m in _CARD_RE.finditer(text):
        digits = re.sub(r"[ -]", "", m.group())
        if len(digits) >= 13 and _luhn(digits):
            hits.append(GuardrailHit(
                category="PCI",
                kind="card_number",
                redacted=text.replace(m.group(), "**** **** **** ****"),
            ))

    # --- PCI: CVV ---
    for m in _CVV_RE.finditer(text):
        hits.append(GuardrailHit(
            category="PCI",
            kind="cvv_code",
            redacted=text.replace(m.group(), "[CVV REDACTED]"),
        ))

    # --- PCI: expiry ---
    for m in _EXPIRY_RE.finditer(text):
        hits.append(GuardrailHit(
            category="PCI",
            kind="card_expiry",
            redacted=text.replace(m.group(), "[EXPIRY REDACTED]"),
        ))

    # --- PII: SSN ---
    for m in _SSN_RE.finditer(text):
        hits.append(GuardrailHit(
            category="PII",
            kind="ssn",
            redacted=text.replace(m.group(), "***-**-****"),
        ))

    # --- PII: phone ---
    for m in _PHONE_RE.finditer(text):
        hits.append(GuardrailHit(
            category="PII",
            kind="phone_number",
            redacted=text.replace(m.group(), "[PHONE REDACTED]"),
        ))

    # --- PII: password ---
    for m in _PASSWORD_RE.finditer(text):
        hits.append(GuardrailHit(
            category="PII",
            kind="password",
            redacted=re.sub(_PASSWORD_RE, "[PASSWORD REDACTED]", text),
        ))

    return hits


SAFE_RESPONSE = (
    "For your security, please don't share payment card numbers, CVV codes, "
    "Social Security Numbers, passwords, or other sensitive personal information "
    "in this chat. I can help you with order status, returns, and policy questions "
    "without needing that information."
)
