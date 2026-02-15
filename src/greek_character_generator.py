import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")

CHARACTER_PROMPTS = {
    "alpha_beta": """You are writing a script for an educational video featuring two cute Greek letter characters.
The characters are: Alpha (α) and Beta (β) - two little Greek letter creatures with big round eyes, small arms and legs, curious student personalities. Alpha is confident and loves explaining, Beta is curious and asks questions. They look at the main educational image together as students.
Format: The script should have both characters talking to each other, with questions and answers. Include [IMAGE: description] markers at key moments.""",
    "gamma_delta": """You are writing a script for an educational video featuring two cute Greek letter characters.
The characters are: Gamma (γ) and Delta (δ) - two little Greek letter creatures with big round eyes, small arms and legs, curious student personalities. Gamma is enthusiastic and loves discoveries, Delta is thoughtful and makes connections. They look at the main educational image together as students.
Format: The script should have both characters talking to each other, with questions and answers. Include [IMAGE: description] markers at key moments.""",
    "epsilon_zeta": """You are writing a script for an educational video featuring two cute Greek letter characters.
The characters are: Epsilon (ε) and Zeta (ζ) - two little Greek letter creatures with big round eyes, small arms and legs, curious student personalities. Epsilon is energetic and gets excited, Zeta is calm and explains carefully. They look at the main educational image together as students.
Format: The script should have both characters talking to each other, with questions and answers. Include [IMAGE: description] markers at key moments.""",
    "theta_lambda": """You are writing a script for an educational video featuring two cute Greek letter characters.
The characters are: Theta (θ) and Lambda (λ) - two little Greek letter creatures with big round eyes, small arms and legs, curious student personalities. Theta is creative and makes analogies, Lambda is logical and organized. They look at the main educational image together as students.
Format: The script should have both characters talking to each other, with questions and answers. Include [IMAGE: description] markers at key moments.""",
}

CHARACTER_IMAGE_STYLES = {
    "alpha_beta": "two cute Greek letters α and β with big round eyes, small arms and legs, round fuzzy bodies, student-like expressions, looking curious, cartoon style, pastel blue and pink colors, educational cute",
    "gamma_delta": "two cute Greek letters γ and δ with big round eyes, small arms and legs, round fuzzy bodies, student-like expressions, looking curious, cartoon style, pastel green and orange colors, educational cute",
    "epsilon_zeta": "two cute Greek letters ε and ζ with big round eyes, small arms and legs, round fuzzy bodies, student-like expressions, looking curious, cartoon style, pastel purple and yellow colors, educational cute",
    "theta_lambda": "two cute Greek letters θ and λ with big round eyes, small arms and legs, round fuzzy bodies, student-like expressions, looking curious, cartoon style, pastel cyan and magenta colors, educational cute",
}


def generate_script_with_character(
    topic: str, research_data: list[dict], character: str = "alpha_beta"
) -> str:
    """Generate an educational video script with Greek letter characters."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    context = "\n\n".join(
        [
            f"Source {i + 1}: {r.get('title', '')}\n{r.get('text', '')}"
            for i, r in enumerate(research_data[:5])
        ]
    )

    system_prompt = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["alpha_beta"])

    user_prompt = f"""Topic: {topic}

Research sources:
{context}

Write an educational script (about 2-3 minutes) where two Greek letter students learn about this topic together. Have them ask questions and explain to each other. Include [IMAGE: description] markers where the visual shows the concept they're learning about."""

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
    """Generate an image with Greek letter characters included."""
    import base64
    import requests

    char_style = CHARACTER_IMAGE_STYLES.get(
        character, CHARACTER_IMAGE_STYLES["alpha_beta"]
    )

    full_prompt = f"""{prompt}. In the corner, show two small Greek letter character students watching and learning: {char_style}. They should be looking at the main image with curious student expressions.
Style: cute cartoon, educational, soft colors, dark background for the main content,
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
