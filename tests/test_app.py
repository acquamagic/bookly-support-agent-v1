import unittest

import app


class AppHtmlTests(unittest.TestCase):
    def test_v2_voice_controls_are_rendered(self):
        self.assertIn('id="web-chat-mode"', app.HTML)
        self.assertIn('id="voice-chat-mode"', app.HTML)
        self.assertIn('id="voice"', app.HTML)
        self.assertIn("SpeechRecognition", app.HTML)
        self.assertIn("speechSynthesis", app.HTML)

    def test_web_chat_is_default_mode(self):
        self.assertIn('id="web-chat-mode" class="mode-button active"', app.HTML)
        self.assertIn('aria-pressed="true"', app.HTML)


if __name__ == "__main__":
    unittest.main()
