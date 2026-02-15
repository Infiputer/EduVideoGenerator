import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")


def generate_image(prompt: str, output_path: str, size: str = "256x256") -> str:
    """Generate an image using NanoGPT image API with cartoon/pixar style."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    cartoon_prompt = f"""{prompt}, 
Style: Pixar animation, cute cartoon, colorful, whimsical, 
animated movie quality, children's book illustration, 
soft colors, 3D render but not photorealistic, 
friendly and warm atmosphere. NO realistic human faces."""

    headers = {
        "Authorization": f"Bearer {NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "hidream",
        "prompt": cartoon_prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json",
    }

    try:
        print(f"  Generating image: {prompt[:50]}...")
        response = requests.post(
            f"{NANO_GPT_BASE_URL}/images/generations",
            headers=headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        image_bytes = base64.b64decode(result["data"][0]["b64_json"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        print(f"  Saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  Image generation failed: {e}")
        raise
