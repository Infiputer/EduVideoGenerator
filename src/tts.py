import asyncio
import os
import uuid
import edge_tts
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")

VOICES = {
    "female": "en-US-JennyNeural",
    "male": "en-US-GuyNeural",
    "casual": "en-US-AriaNeural",
}


async def generate_speech_edge(
    text: str, output_path: str, voice: str = "female"
) -> str:
    """Generate speech using Edge TTS (free, high quality)."""
    voice_name = VOICES.get(voice, VOICES["female"])

    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)
    return output_path


def generate_speech_nano(text: str, output_path: str) -> str:
    """Generate speech using NanoGPT TTS API."""
    import requests

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "tts-1",
        "input": text[:4096],
        "voice": "alloy",
        "response_format": "mp3",
    }

    response = requests.post(
        f"{NANO_GPT_BASE_URL}/audio/speech", headers=headers, json=data, timeout=60
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


async def generate_speech(
    text: str, output_dir: str, use_nano: bool = False, voice: str = "female"
) -> list[dict]:
    """Split text into chunks and generate speech for each."""
    import math

    max_chars = 4500
    chunks = []

    sentences = text.replace("\n", " ").split(". ")
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    audio_files = []

    for i, chunk in enumerate(chunks):
        filename = f"chunk_{i:03d}.mp3"
        filepath = os.path.join(output_dir, filename)

        try:
            if use_nano:
                generate_speech_nano(chunk, filepath)
            else:
                await generate_speech_edge(chunk, filepath, voice)

            audio_files.append({"file": filepath, "text": chunk, "index": i})
            print(f"Generated audio chunk {i + 1}/{len(chunks)}")
        except Exception as e:
            print(f"Failed to generate chunk {i}: {e}")

    return audio_files
