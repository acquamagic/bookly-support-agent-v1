"""
Tests for PII / PCI guardrails.
Covers detection, Luhn validation, false-positive avoidance,
and end-to-end agent blocking.
"""
from __future__ import annotations

import unittest

from bookly_agent.guardrails import check
from bookly_agent.orchestrator import AgentState, BooklySupportAgent


class TestPCICardNumber(unittest.TestCase):
    def _kinds(self, text):
        return [h.kind for h in check(text)]

    def test_detects_spaced_visa(self):
        self.assertIn("card_number", self._kinds("my card is 4111 1111 1111 1111"))

    def test_detects_dashed_card(self):
        self.assertIn("card_number", self._kinds("4111-1111-1111-1111"))

    def test_detects_continuous_card(self):
        self.assertIn("card_number", self._kinds("4111111111111111"))

    def test_detects_amex(self):
        # Valid Amex test number (15 digits)
        self.assertIn("card_number", self._kinds("378282246310005"))

    def test_ignores_order_id(self):
        # BLY-1001 should never trigger card detection
        self.assertEqual([], check("my order is BLY-1001"))

    def test_ignores_random_digits(self):
        # 8-digit number that fails Luhn should not trigger
        self.assertEqual([], check("reference number 12345678"))

    def test_luhn_false_positive_rejected(self):
        # 16 digits that fail Luhn
        self.assertEqual([], check("1234 5678 9012 3456"))


class TestPCICVV(unittest.TestCase):
    def test_detects_cvv_keyword(self):
        hits = check("cvv is 123")
        self.assertTrue(any(h.kind == "cvv_code" for h in hits))

    def test_detects_cvc_keyword(self):
        hits = check("CVC: 456")
        self.assertTrue(any(h.kind == "cvv_code" for h in hits))

    def test_detects_security_code(self):
        hits = check("security code 9876")
        self.assertTrue(any(h.kind == "cvv_code" for h in hits))


class TestPCIExpiry(unittest.TestCase):
    def test_detects_expiry(self):
        hits = check("expiry 12/26")
        self.assertTrue(any(h.kind == "card_expiry" for h in hits))

    def test_detects_valid_thru(self):
        hits = check("valid thru 06/2027")
        self.assertTrue(any(h.kind == "card_expiry" for h in hits))


class TestPIISSN(unittest.TestCase):
    def test_detects_ssn_dashes(self):
        hits = check("my SSN is 123-45-6789")
        self.assertTrue(any(h.kind == "ssn" for h in hits))

    def test_ignores_invalid_ssn_prefix(self):
        # 000 prefix is invalid
        self.assertEqual([], check("000-45-6789"))


class TestPIIPhone(unittest.TestCase):
    def test_detects_us_phone(self):
        hits = check("call me at 415-555-0192")
        self.assertTrue(any(h.kind == "phone_number" for h in hits))

    def test_detects_parentheses_format(self):
        hits = check("(415) 555-0192")
        self.assertTrue(any(h.kind == "phone_number" for h in hits))

    def test_detects_country_code(self):
        hits = check("+1 415 555 0192")
        self.assertTrue(any(h.kind == "phone_number" for h in hits))


class TestPIIPassword(unittest.TestCase):
    def test_detects_password_is(self):
        hits = check("my password is hunter2")
        self.assertTrue(any(h.kind == "password" for h in hits))

    def test_detects_passcode(self):
        hits = check("passcode: abc123")
        self.assertTrue(any(h.kind == "password" for h in hits))


class TestAgentBlocking(unittest.TestCase):
    """Guardrail should block message before intent routing or tool calls."""

    def setUp(self):
        self.agent = BooklySupportAgent()

    def test_card_number_blocked(self):
        result = self.agent.handle("my card is 4111 1111 1111 1111", AgentState())
        self.assertIn("security", result.response.lower())
        # Trace must contain the guardrail block step
        types = [(s["type"], s["name"]) for s in result.trace]
        self.assertIn(("guardrail", "pii_pci_blocked"), types)

    def test_ssn_blocked(self):
        result = self.agent.handle("SSN 123-45-6789", AgentState())
        self.assertIn("guardrail", result.response.lower() + " ".join(
            s["type"] for s in result.trace
        ))

    def test_clean_message_passes_through(self):
        result = self.agent.handle("Where is my order?", AgentState())
        # Should NOT be blocked — normal clarifier response expected
        self.assertNotIn("security", result.response.lower())
        types = [s["type"] for s in result.trace]
        self.assertNotIn("pii_pci_blocked", " ".join(types))


if __name__ == "__main__":
    unittest.main()
