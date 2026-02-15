import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")


def generate_deep_dive_script(topic: str, research_data: list[dict]) -> str:
    """Generate an in-depth educational script like 3Blue1Brown style."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    context = "\n\n".join(
        [
            f"Source {i + 1}: {r.get('title', '')}\n{r.get('text', '')}"
            for i, r in enumerate(research_data[:8])
        ]
    )

    system_prompt = """You are an expert educator creating a deep-dive educational video script in the style of 3Blue1Brown.

Write an engaging, technically accurate script that:
- Starts with an intuitive visual analogy/intuition before diving into details
- Uses specific numbers and concrete examples
- Explains NOT just WHAT happens but WHY it happens
- Makes connections to related concepts
- Uses narrative flow - each idea builds on the previous
- Includes [IMAGE: description] markers for key visual concepts

IMPORTANT FORMATTING RULES:
- NO symbols at all: do NOT use **bold**, *italics*, or any special characters
- Write all numbers as words: say "two million" not "2,000,000", say "one thousand five hundred" not "1,500"
- Plain text only, no markdown formatting

The script should be 2-3 minutes when read aloud (about 350-500 words).

Tone: Curious, precise, enthusiastic about the beauty of the concepts."""

    user_prompt = f"""Topic: {topic}

Research sources:
{context}

Write a deep-dive educational script that explains the fundamental principles. Start with an intuition-building analogy, then explain the technical details. Include [IMAGE: description] markers at key moments where visuals would help understanding."""

    headers = {
        "Authorization": f"Bearer {NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "moonshotai/kimi-k2.5:thinking",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 3000,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            f"{NANO_GPT_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Script generation failed: {e}")
        # Retry
        try:
            print("  Retrying...")
            response = requests.post(
                f"{NANO_GPT_BASE_URL}/chat/completions",
                headers=headers,
                json=data,
                timeout=180,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e2:
            print(f"Script generation failed on retry: {e2}")
            raise


# Character prompts for A and B
CHARACTER_PROMPTS = {
    "letter_AB": """You are writing a script for an educational video featuring two cute letter characters.
The characters are: Letter A and Letter B - capital letters with big round eyes, small arms and legs, cute student personalities. They watch the main educational image together and react to what they're learning.
Format: Single narrator educational script (not dialogue). Include [IMAGE: description] markers at key moments.""",
}

CHARACTER_IMAGE_STYLES = {
    "letter_AB": "two cute capital letters A and B with big round eyes, small arms and legs, round friendly bodies, student-like expressions, looking curious and interested, cartoon style, letter A in blue color, letter B in pink color, standing together watching the main image, cute educational",
}


def generate_image_with_characters(
    prompt: str, output_path: str, size: str = "1920x1080"
) -> str:
    """Generate an HD image with letter characters watching the main content."""
    import base64

    char_style = CHARACTER_IMAGE_STYLES["letter_AB"]

    full_prompt = f"""{prompt}. In the corner, show two cute letter characters watching and learning: {char_style}. They should be looking at the main educational content with curious student expressions.
Style: 3Blue1Brown educational style, dark navy background (#0a0a1a), clean mathematical visuals, neon accent colors (cyan, magenta, yellow), 3D render but not photorealistic, friendly warm atmosphere, high quality detailed."""

    headers = {
        "Authorization": f"Bearer {NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "hidream",
        "prompt": full_prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json",
    }

    try:
        print(f"  Generating HD image: {prompt[:50]}...")
        response = requests.post(
            f"{NANO_GPT_BASE_URL}/images/generations",
            headers=headers,
            json=data,
            timeout=90,
        )
        response.raise_for_status()
        result = response.json()

        image_bytes = base64.b64decode(result["data"][0]["b64_json"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        print(f"  ✓ Saved HD image: {output_path} ({len(image_bytes) // 1024}KB)")
        return output_path

    except Exception as e:
        print(f"  Image gen failed: {e}")
        from src.video_generator import create_dark_slide

        create_dark_slide(prompt, output_path, width=1920, height=1080)
        return output_path
