import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")


def generate_script_with_images(topic: str, research_data: list[dict]) -> str:
    """Generate an educational video script with embedded image prompts."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    context = "\n\n".join(
        [
            f"Source {i + 1}: {r.get('title', '')}\n{r.get('text', '')}"
            for i, r in enumerate(research_data[:5])
        ]
    )

    system_prompt = """You are an educational video script writer. Create an engaging educational video script.

Rules:
- Split the script into 5-7 segments (one for each main point)
- At natural transition points, embed image prompts in format: [IMAGE: description of what to show]
- The audio should describe/explain what's shown in the image
- Keep each segment 2-4 sentences for the audio
- Total script should be 2-3 minutes when read aloud
- Use a dark background style (3Blue1Brown aesthetic) for image prompts
- Include visualizations, diagrams, not realistic humans

Example format:
"Let's start with the basics. [IMAGE: bright atom with electron orbiting nucleus, neon colors against dark background]

Now here's where it gets interesting. [IMAGE: wave function probability cloud, purple and blue gradients, dark background]

This is called superposition. [IMAGE: particle in multiple states simultaneously, colorful superposition visualization]" """

    user_prompt = f"""Topic: {topic}

Research sources:
{context}

Write an educational video script with image prompts embedded at key moments."""

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
        "max_tokens": 2500,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            f"{NANO_GPT_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Script generation failed: {e}")
        raise


def parse_script(script: str) -> list[dict]:
    """Parse script into segments with text and image prompts."""
    pattern = r"\[IMAGE: ([^\]]+)\]"
    parts = re.split(pattern, script)

    segments = []

    for i in range(0, len(parts), 2):
        text = parts[i].strip()
        if not text:
            continue

        image_prompt = ""
        if i + 1 < len(parts):
            image_prompt = parts[i + 1].strip()

        if text:
            segments.append({"text": text, "image_prompt": image_prompt})

    return segments


def generate_slide_topics(script: str) -> list[str]:
    """Legacy function - kept for compatibility."""
    segments = parse_script(script)
    return [s["image_prompt"] or f"Part {i + 1}" for i, s in enumerate(segments)]


# Legacy function
def generate_script(topic: str, research_data: list[dict]) -> str:
    """Legacy wrapper for compatibility."""
    return generate_script_with_images(topic, research_data)
