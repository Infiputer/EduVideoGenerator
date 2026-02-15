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
from src.script_generator import generate_script_with_images, parse_script
from src.tts import generate_speech
from src.video_generator import create_video_with_segments

load_dotenv()

OUTPUT_DIR = "output"


def main():
    parser = argparse.ArgumentParser(description="Educational Video Generator")
    parser.add_argument("topic", help="Topic for the educational video")
    parser.add_argument(
        "--voice",
        choices=["female", "male", "casual"],
        default="female",
        help="TTS voice",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image generation (use dark slides)",
    )
    parser.add_argument(
        "--use-nano-tts",
        action="store_true",
        help="Use NanoGPT TTS instead of Edge TTS",
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
    logger.info("EduVideoGenerator - 3Blue1Brown Style")
    logger.info("=" * 60)
    logger.info(f"Topic: {topic}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Images: {'Disabled' if args.no_images else 'Enabled'}")
    logger.info(f"Voice: {args.voice}")
    logger.info("")

    # Step 1: Research
    logger.info("[STEP 1] Researching topic with Exa AI...")
    try:
        research_data = search(topic, num_results=5)
        logger.info(f"  Found {len(research_data)} sources")
        for r in research_data[:3]:
            logger.info(f"    - {r.get('title', 'Untitled')[:60]}")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        research_data = []
    logger.info("")

    # Step 2: Generate script with embedded image prompts
    logger.info("[STEP 2] Generating script with image prompts (Kimi K2.5)...")
    try:
        script = generate_script_with_images(topic, research_data)
        logger.info(f"  Script generated ({len(script)} chars)")
        logger.info(f"  Preview:\n{script[:300]}...")
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        script = f"This video is about {topic}."
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
                seg.get("image_prompt", "none")[:40]
                if seg.get("image_prompt")
                else "none"
            )
            logger.info(
                f"    Segment {i + 1}: {seg['text'][:40]}... | Image: {img_desc}"
            )
    except Exception as e:
        logger.error(f"Parse failed: {e}")
        segments = [{"text": script, "image_prompt": topic}]
    logger.info("")

    # Step 4: Generate video with synced audio + images
    logger.info("[STEP 4] Generating video with synced audio + images...")
    try:
        video_path = os.path.join(output_dir, "video.mp4")
        create_video_with_segments(segments, video_path, use_images=not args.no_images)

        video_size = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"  Video file: {video_path} ({video_size:.1f} MB)")
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        logger.info("  Check output directory for partial results")

    logger.info("")
    logger.info("=" * 60)
    logger.info("DONE!")
    logger.info(f"  Script: {script_path}")
    logger.info(f"  Output dir: {output_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
