import os
import re
import requests
import json
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")


def generate_animated_script(topic: str, research_data: list[dict]) -> list[dict]:
    """Generate an in-depth educational script with animation keyframes for A & B characters."""

    if not NANO_GPT_API_KEY:
        raise ValueError("NANO_GPT_API_KEY not set")

    context = "\n\n".join(
        [
            f"Source {i + 1}: {r.get('title', '')}\n{r.get('text', '')}"
            for i, r in enumerate(research_data[:8])
        ]
    )

    system_prompt = """You are an expert educator creating a deep-dive educational video script with animation keyframes.

IMPORTANT FORMATTING RULES:
- NO symbols: do NOT use **bold**, *italics*, or any markdown
- Write all numbers as words: "two million" not "2,000,000"
- Plain text only

The script will have NINE to TEN segments (keyframes), each about 15-20 seconds of narration.

For each segment, provide:
1. narration: The spoken audio text (2-4 sentences, readable in 15-20 seconds)
2. keyframe_image: Description of what the image should show at this moment in the animation
3. keyframe_state: Position and expression for Letter A and Letter B at this keyframe

Character Design:
- Letter A: blue chibi character with big round eyes connected above the letter, small body
- Letter B: pink chibi character with big round eyes connected above the letter, small body

Positions: left, center-left, center, center-right, right
Expressions: curious, happy, thinking, surprised, excited, concerned

Output format: Return ONLY a JSON array, no other text. Each element:
{
  "narration": "the spoken text",
  "keyframe_image": "description of the visual for this keyframe",
  "A_position": "left/center-left/center/center-right/right",
  "A_expression": "curious/happy/thinking/surprised/excited/concerned",
  "B_position": "left/center-left/center/center-right/right", 
  "B_expression": "curious/happy/thinking/surprised/excited/concerned"
}

Example:
[
  {"narration": "Welcome to this exploration of how the internet works.", "keyframe_image": "Wide shot of a cozy classroom with letters A and B sitting at desks", "A_position": "center-left", "A_expression": "curious", "B_position": "center-right", "B_expression": "curious"},
  {"narration": "Imagine you need to send a huge library of books to someone across the country.", "keyframe_image": "Animation of a large stack of colorful books being loaded onto a truck", "A_position": "left", "A_expression": "surprised", "B_position": "right", "B_expression": "thinking"}
]"""

    user_prompt = f"""Topic: {topic}

Research sources:
{context}

Create a deep-dive educational script with exactly 10 keyframe segments. Each segment should be 15-20 seconds of narration. Include animation states for characters A and B at each keyframe."""

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
        "max_tokens": 4000,
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
        content = result["choices"][0]["message"]["content"]

        # Parse JSON from response
        # Find JSON array in response
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            segments = json.loads(json_match.group())
            return segments
        else:
            raise ValueError("No JSON found in response")

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
            content = result["choices"][0]["message"]["content"]
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                segments = json.loads(json_match.group())
                return segments
        except Exception as e2:
            print(f"Script generation failed on retry: {e2}")
            raise


def generate_image_from_keyframe(
    keyframe_data: dict, segment_num: int, output_path: str, size: str = "1920x1080"
) -> str:
    """Generate a keyframe image with A & B characters in specified states."""
    import base64

    # Build character descriptions
    a_pos = keyframe_data.get("A_position", "center-left")
    a_expr = keyframe_data.get("A_expression", "curious")
    b_pos = keyframe_data.get("B_position", "center-right")
    b_expr = keyframe_data.get("B_expression", "curious")

    # Character style
    a_style = f"chibi letter A with big round eyes, {a_expr} expression, blue color, small body, cartoon style, positioned on {a_pos}"
    b_style = f"chibi letter B with big round eyes, {b_expr} expression, pink color, small body, cartoon style, positioned on {b_pos}"

    # Full prompt
    full_prompt = f"""{keyframe_data.get("keyframe_image", "")}. 

In the scene also show: {a_style}. {b_style}.

Style: 3Blue1Brown educational cartoon, dark navy background, clean mathematical visuals, neon accent colors, 3D render but not photorealistic, high quality detailed 1920x1080."""

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
        print(
            f"  Generating keyframe {segment_num}: {keyframe_data.get('keyframe_image', '')[:50]}..."
        )
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

        print(f"  ✓ Saved: {output_path} ({len(image_bytes) // 1024}KB)")
        return output_path

    except Exception as e:
        print(f"  Image gen failed: {e}")
        from src.video_generator import create_dark_slide

        create_dark_slide(
            keyframe_data.get("keyframe_image", "Keyframe"),
            output_path,
            width=1920,
            height=1080,
        )
        return output_path
