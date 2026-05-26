"""
V3 voice-provider integration tests.

These tests make real HTTP calls to Deepgram and ElevenLabs to verify that
the API keys in .env are valid and the providers respond correctly.

Run with:
    pytest tests/test_voice_providers.py -v
"""
from __future__ import annotations

import os
import unittest

from dotenv import load_dotenv

load_dotenv()

from bookly_agent import voice_providers  # noqa: E402


# Minimal silent WAV (44 bytes): 1 ch, 44100 Hz, 16-bit, 0 samples
_SILENT_WAV = bytes([
    0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00,  # RIFF chunk
    0x57, 0x41, 0x56, 0x45,                            # "WAVE"
    0x66, 0x6d, 0x74, 0x20, 0x10, 0x00, 0x00, 0x00,  # fmt  sub-chunk
    0x01, 0x00, 0x01, 0x00,                            # PCM, 1 channel
    0x44, 0xac, 0x00, 0x00, 0x88, 0x58, 0x01, 0x00,  # 44100 Hz, byte rate
    0x02, 0x00, 0x10, 0x00,                            # block align, 16-bit
    0x64, 0x61, 0x74, 0x61, 0x00, 0x00, 0x00, 0x00,  # data sub-chunk (empty)
])

SKIP_DEEPGRAM    = not os.environ.get("DEEPGRAM_API_KEY")
SKIP_ELEVENLABS  = not os.environ.get("ELEVENLABS_API_KEY")


class TestDeepgramKey(unittest.TestCase):
    """Verify the Deepgram API key is present and authenticates successfully."""

    def test_key_present(self):
        self.assertTrue(
            os.environ.get("DEEPGRAM_API_KEY"),
            "DEEPGRAM_API_KEY is not set — add it to .env",
        )

    @unittest.skipIf(SKIP_DEEPGRAM, "DEEPGRAM_API_KEY not set")
    def test_key_authenticates(self):
        """POST a silent WAV; a 200 response means the key is accepted."""
        import requests
        r = requests.post(
            "https://api.deepgram.com/v1/listen",
            headers={
                "Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}",
                "Content-Type": "audio/wav",
            },
            data=_SILENT_WAV,
            timeout=15,
        )
        self.assertEqual(
            r.status_code, 200,
            f"Deepgram returned {r.status_code}: {r.text[:200]}",
        )

    @unittest.skipIf(SKIP_DEEPGRAM, "DEEPGRAM_API_KEY not set")
    def test_transcribe_returns_string(self):
        """deepgram_transcribe() must return a str (empty string is fine for silent audio)."""
        result = voice_providers.deepgram_transcribe(_SILENT_WAV)
        self.assertIsInstance(result, str)


class TestElevenLabsKey(unittest.TestCase):
    """Verify the ElevenLabs API key is present and returns audio."""

    def test_key_present(self):
        self.assertTrue(
            os.environ.get("ELEVENLABS_API_KEY"),
            "ELEVENLABS_API_KEY is not set — add it to .env",
        )

    @unittest.skipIf(SKIP_ELEVENLABS, "ELEVENLABS_API_KEY not set")
    def test_key_authenticates(self):
        """POST a short TTS request; a 200 response means the key is accepted."""
        import requests
        r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL",
            headers={
                "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
                "Content-Type": "application/json",
            },
            json={"text": "OK", "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}},
            timeout=15,
        )
        self.assertEqual(
            r.status_code, 200,
            f"ElevenLabs returned {r.status_code}: {r.text[:200]}",
        )

    @unittest.skipIf(SKIP_ELEVENLABS, "ELEVENLABS_API_KEY not set")
    def test_speak_returns_audio_bytes(self):
        """elevenlabs_speak() must return non-empty bytes (MP3 audio)."""
        audio = voice_providers.elevenlabs_speak("Hello from Bookly.")
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0, "ElevenLabs returned empty audio")

    @unittest.skipIf(SKIP_ELEVENLABS, "ELEVENLABS_API_KEY not set")
    def test_speak_returns_mp3(self):
        """Response should start with the MP3 magic bytes (ID3 or 0xFF 0xFB)."""
        audio = voice_providers.elevenlabs_speak("Test.")
        is_mp3 = audio[:3] == b"ID3" or audio[:2] == b"\xff\xfb"
        self.assertTrue(is_mp3, f"Response doesn't look like MP3 (first bytes: {audio[:4].hex()})")


if __name__ == "__main__":
    unittest.main()
