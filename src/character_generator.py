import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")

CHARACTER_PROMPTS = {
    "fluffy_blue": """You are writing a script for an educational video featuring a cute character.
The character is: A fluffy round blue creature with big round eyes, soft fuzzy texture like a blue teddy bear, small little arms, constantly curious and friendly.
The character should react to the content with emotions - happy when explaining cool things, confused when learning something complex, excited to share knowledge.
Format: The script should be in the character's voice, first person, with reactions and emotions. Include [IMAGE: description] markers at key moments.""",
    "pink_floof": """You are writing a script for an educational video featuring a cute character.
The character is: A round pink fluffy ball with tiny rabbit-like ears, big sparkly eyes, soft pastel pink fur, small stubby legs, always bouncing with energy and enthusiasm.
The character should react to the content - bouncing when excited, tilting head when curious, clapping when happy about a concept.
Format: The script should be in the character's voice, first person, with reactions. Include [IMAGE: description] markers at key moments.""",
    "little_ghost": """You are writing a script for an educational video featuring a cute character.
The character is: A friendly little ghost wisp with a rounded head, big round eyes, tiny little arms, semi-transparent white body with subtle glow, floating slightly above ground, cute and curious.
The character should react - floating up when excited, shimmering when thinking, bobbing when explaining.
Format: The script should be in the character's voice, first person, with reactions. Include [IMAGE: description] markers at key moments.""",
    "bouncy_bubble": """You are writing a script for an educational video featuring a cute character.
The character is: A cute transparent round bubble-like creature with tiny rainbow sparkles inside, small nubby arms, big eyes that reflect the environment, slightly bouncy movements, magical and ethereal.
The character should react - shimmering when happy, wobbling when confused, glowing when excited.
Format: The script should be in the character's voice, first person, with reactions. Include [IMAGE: description] markers at key moments.""",
}

CHARACTER_IMAGE_STYLES = {
    "fluffy_blue": "cute fluffy blue blob creature with big round eyes, soft fuzzy fur texture, small arms, friendly expression, cartoon style, pastel blue with darker blue accents, white belly, round shape",
    "pink_floof": "cute pink fluffy ball creature with tiny ears, big sparkly eyes, soft pastel pink fur, small stubby legs, bouncing pose, cartoon style, pastel pink with darker pink accents",
    "little_ghost": "cute little ghost wisp creature, rounded head, big round eyes, tiny arms, semi-transparent white body with glow, floating, cartoon style, white with subtle blue glow, friendly expression",
    "bouncy_bubble": "cute transparent bubble creature, round shape, tiny nubby arms, big eyes with rainbow sparkles inside, magical ethereal, cartoon style, transparent with rainbow prismatic colors",
}


def generate_script_with_character(
    topic: str, research_data: list[dict], character: str = "fluffy_blue"
) -> str:
    """Generate an educational video script with a specific character."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    context = "\n\n".join(
        [
            f"Source {i + 1}: {r.get('title', '')}\n{r.get('text', '')}"
            for i, r in enumerate(research_data[:5])
        ]
    )

    system_prompt = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["fluffy_blue"])

    user_prompt = f"""Topic: {topic}

Research sources:
{context}

Write an educational script (about 2-3 minutes) that teaches this topic. Include [IMAGE: description] markers where visuals would help explain the concept. Make it fun and educational!"""

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
        "temperature": 0.8,
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
        # Retry once
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


def generate_image_with_character(
    prompt: str, character: str, output_path: str, size: str = "256x256"
) -> str:
    """Generate an image with the cute character included."""
    import base64
    import requests

    char_style = CHARACTER_IMAGE_STYLES.get(
        character, CHARACTER_IMAGE_STYLES["fluffy_blue"]
    )

    full_prompt = f"""{prompt}. Also include: {char_style}. 
Style: cute cartoon, kawaii, soft colors, dark educational background,
3D render but not photorealistic, friendly and warm atmosphere."""

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
        print(f"  Generating image: {prompt[:40]}...")
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

        print(f"  ✓ Saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  Image gen failed: {e}")
        from src.video_generator import create_dark_slide

        create_dark_slide(prompt, output_path)
        return output_path
