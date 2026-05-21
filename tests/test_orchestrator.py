import unittest

from bookly_agent.orchestrator import AgentState, BooklySupportAgent


class BooklySupportAgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = BooklySupportAgent()

    def test_order_status_multi_turn(self):
        state = AgentState()
        first = self.agent.handle("Where is my order?", state)
        self.assertIn("order number", first.response)
        self.assertEqual(first.state.pending_intent, "order_status")

        second = self.agent.handle("BLY-1001", first.state)
        self.assertIn("In transit", second.response)
        self.assertTrue(any(step["name"] == "lookup_order" for step in second.trace))

    def test_return_creation_multi_turn(self):
        first = self.agent.handle("I want to return BLY-1002")
        self.assertIn("reason", first.response)

        second = self.agent.handle("damaged", first.state)
        self.assertIn("created return", second.response.lower())
        self.assertTrue(any(step["name"] == "create_return" for step in second.trace))

    def test_ambiguous_order_asks_clarifying_question(self):
        result = self.agent.handle("I need help with my order")
        self.assertIn("order status", result.response)
        self.assertFalse(any(step["type"] == "tool" for step in result.trace))


if __name__ == "__main__":
    unittest.main()

