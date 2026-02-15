import os
import base64
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from dotenv import load_dotenv

load_dotenv()

NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")
NANO_GPT_BASE_URL = os.getenv("NANO_GPT_BASE_URL", "https://nano-gpt.com/api/v1")


def generate_image(prompt: str, output_path: str, size: str = "256x256") -> str:
    """Generate an image using NanoGPT image API with 3Blue1Brown/dark style."""

    if not NANO_GPT_API_KEY:
        print(f"  [WARN] No API key, creating fallback dark slide")
        create_dark_slide(prompt, output_path)
        return output_path

    dark_style_prompt = f"""{prompt}, 
Style: mathematical visualization, 3Blue1Brown, 
dark navy/black background (#0a0a1a), 
neon accent colors (cyan, magenta, yellow, purple),
geometric shapes, flowing animations aesthetic,
clean minimal design, glowing lines, 
educational diagram, not photorealistic, cartoon style."""

    headers = {
        "Authorization": f"Bearer {NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "hidream",
        "prompt": dark_style_prompt,
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
        print(f"  Image gen failed: {e}, using fallback")
        create_dark_slide(prompt, output_path)
        return output_path


def create_dark_slide(
    text: str, output_path: str, width: int = 1280, height: int = 720
):
    """Create a dark mode slide with text (fallback when image gen fails)."""
    img = Image.new("RGB", (width, height), color=(10, 10, 26))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42
        )
        font_text = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
        )
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font_text)
        if bbox[2] - bbox[0] < width - 100:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    title = text[:50] + "..." if len(text) > 50 else text
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((title_x, 150), title, font=font_title, fill=(100, 200, 255))

    y_offset = 280
    for line in lines[:4]:
        bbox = draw.textbbox((0, 0), line, font=font_text)
        text_x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((text_x, y_offset), line, font=font_text, fill=(200, 200, 220))
        y_offset += 40

    img.save(output_path)


def estimate_duration(text: str, words_per_minute: float = 150) -> float:
    """Estimate video duration based on text length."""
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return max(2.0, minutes * 60)


def create_video_with_segments(
    segments: list[dict], output_path: str, use_images: bool = True
) -> str:
    """Create video from script segments (text + image prompts).

    Each segment has:
    - text: the narration
    - image_prompt: what image to show

    The audio and image are synced - each image shows while its narration plays.
    """
    if not segments:
        raise ValueError("No segments provided")

    video_clips = []

    for i, segment in enumerate(segments):
        text = segment.get("text", "")
        image_prompt = segment.get("image_prompt", f"Part {i + 1}")

        print(f"\n[Segment {i + 1}/{len(segments)}]")
        print(f"  Text: {text[:80]}...")
        print(f"  Image prompt: {image_prompt}")

        # Generate audio for this segment
        import asyncio
        from src.tts import generate_speech_edge

        audio_path = os.path.join(os.path.dirname(output_path), f"segment_{i:03d}.mp3")

        async def gen_audio():
            await generate_speech_edge(text, audio_path, "female")

        asyncio.run(gen_audio())

        if not os.path.exists(audio_path):
            print(f"  [WARN] Audio not generated, skipping segment")
            continue

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        print(f"  Audio duration: {duration:.1f}s")

        # Generate or create image
        image_path = os.path.join(os.path.dirname(output_path), f"slide_{i:03d}.png")

        if use_images and NANO_GPT_API_KEY:
            try:
                generate_image(image_prompt, image_path, size="256x256")
            except:
                create_dark_slide(image_prompt, image_path)
        else:
            create_dark_slide(image_prompt, image_path)

        # Create video clip: image for duration of audio
        image_clip = ImageClip(image_path).with_duration(duration)
        image_clip = image_clip.with_audio(audio_clip)

        video_clips.append(image_clip)
        print(f"  ✓ Segment {i + 1} ready ({duration:.1f}s)")

    if not video_clips:
        raise ValueError("No video clips created")

    print(f"\n[Combining {len(video_clips)} segments into video...]")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Using CPU encoding for reliability
    print("  Using CPU encoding (libx264)...")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    print(f"✓ Video saved: {output_path}")
    return output_path


# Legacy functions
def create_video(audio_files: list[dict], slide_topics: list[str], output_path: str):
    """Legacy function - redirects to new segment-based approach."""
    pass


def create_video_simple(audio_files: list[dict], output_path: str):
    """Legacy function."""
    pass
