import os
import requests

# Minimal Deepgram STT integration (sync, not streaming)
def deepgram_transcribe(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPGRAM_API_KEY not set")
    response = requests.post(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": mime_type,
        },
        data=audio_bytes
    )
    if not response.ok:
        raise RuntimeError(
            f"{response.status_code} {response.reason} — {response.text[:300]}"
        )
    channels = response.json().get("results", {}).get("channels", [])
    if not channels or not channels[0].get("alternatives"):
        return ""
    return channels[0]["alternatives"][0].get("transcript", "")

# Minimal ElevenLabs TTS integration (sync, not streaming)
def elevenlabs_speak(text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bytes:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    response = requests.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json=payload
    )
    response.raise_for_status()
    return response.content

# Usage example (for demo, not wired to UI):
# with open("audio.webm", "rb") as f:
#     transcript = deepgram_transcribe(f.read())
# audio_bytes = elevenlabs_speak("Hello, world!")
# with open("output.mp3", "wb") as f:
#     f.write(audio_bytes)
