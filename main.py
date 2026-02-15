import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from src.research import search
from src.script_generator import parse_script
from src.letter_generator import (
    generate_deep_dive_script,
    generate_image_with_characters,
)
from src.tts import generate_speech_edge
from src.video_generator import create_dark_slide

load_dotenv()

OUTPUT_DIR = "output"
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080


def main():
    parser = argparse.ArgumentParser(
        description="Educational Video Generator - 3Blue1Brown Style"
    )
    parser.add_argument("topic", help="Topic for the educational video")
    parser.add_argument(
        "--voice",
        choices=["female", "male", "casual"],
        default="female",
        help="TTS voice",
    )
    parser.add_argument(
        "--no-images", action="store_true", help="Skip image generation"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    topic = args.topic
    run_id = f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(output_dir, exist_ok=True)

    logger.info("=" * 60)
    logger.info(f"EduVideoGenerator - Letter A & B Style (HD)")
    logger.info("=" * 60)
    logger.info(f"Topic: {topic}")
    logger.info(f"Resolution: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Images: {'Disabled' if args.no_images else 'Enabled'}")
    logger.info("")

    # Step 1: Research
    logger.info("[STEP 1] Researching topic with Exa AI...")
    try:
        research_data = search(topic, num_results=8)  # More sources for deeper content
        logger.info(f"  Found {len(research_data)} sources")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        research_data = []
    logger.info("")

    # Step 2: Generate deep dive script
    logger.info("[STEP 2] Generating deep dive script (3Blue1Brown style)...")
    try:
        script = generate_deep_dive_script(topic, research_data)
        logger.info(f"  Script generated ({len(script)} chars)")
        logger.info(f"  Preview:\n{script[:400]}...")
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        script = f"Let me tell you about {topic}."
    logger.info("")

    # Save script
    script_path = os.path.join(output_dir, "script.txt")
    with open(script_path, "w") as f:
        f.write(script)
    logger.info(f"  Script saved: {script_path}")
    logger.info("")

    # Step 3: Parse into segments
    logger.info("[STEP 3] Parsing script into segments...")
    try:
        segments = parse_script(script)
        logger.info(f"  Found {len(segments)} segments")
        for i, seg in enumerate(segments):
            img_desc = (
                seg.get("image_prompt", "none")[:50]
                if seg.get("image_prompt")
                else "none"
            )
            logger.info(
                f"    Segment {i + 1}: {seg['text'][:50]}... | Image: {img_desc}"
            )
    except Exception as e:
        logger.error(f"Parse failed: {e}")
        segments = [{"text": script, "image_prompt": topic}]
    logger.info("")

    # Step 4: Generate video
    logger.info("[STEP 4] Generating HD video with synced audio + images...")

    video_clips = []
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

    for i, segment in enumerate(segments):
        text = segment.get("text", "")
        image_prompt = segment.get("image_prompt", f"Part {i + 1}")

        logger.info(f"\n[Segment {i + 1}/{len(segments)}]")
        logger.info(f"  Text: {text[:60]}...")

        # Generate audio
        audio_path = os.path.join(output_dir, f"segment_{i:03d}.mp3")
        asyncio.run(generate_speech_edge(text, audio_path, args.voice))

        if not os.path.exists(audio_path):
            logger.error(f"  Audio not generated, skipping")
            continue

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        logger.info(f"  Audio duration: {duration:.1f}s")

        # Generate HD image
        image_path = os.path.join(output_dir, f"slide_{i:03d}.png")
        if not args.no_images:
            generate_image_with_characters(image_prompt, image_path, size="1920x1080")
        else:
            create_dark_slide(
                image_prompt, image_path, width=IMAGE_WIDTH, height=IMAGE_HEIGHT
            )

        # Create video clip
        image_clip = ImageClip(image_path).with_duration(duration)
        image_clip = image_clip.with_audio(audio_clip)
        video_clips.append(image_clip)
        logger.info(f"  ✓ Segment {i + 1} ready ({duration:.1f}s)")

    # Combine into video
    logger.info(f"\n[Combining {len(video_clips)} segments into HD video...]")
    final_video = concatenate_videoclips(video_clips, method="compose")

    video_path = os.path.join(output_dir, "video.mp4")
    logger.info("  Encoding video...")
    final_video.write_videofile(
        video_path, fps=24, codec="libx264", audio_codec="aac", bitrate="4000k"
    )

    video_size = os.path.getsize(video_path) / (1024 * 1024)
    logger.info(f"  ✓ Video saved: {video_path} ({video_size:.1f} MB)")

    logger.info("")
    logger.info("=" * 60)
    logger.info("DONE!")
    logger.info(f"  Script: {script_path}")
    logger.info(f"  Video: {video_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
