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
from src.animated_generator import (
    generate_animated_script,
    generate_image_from_keyframe,
)
from src.tts import generate_speech_edge
from src.interpolation import generate_animation_sequence, create_video_from_frames

load_dotenv()

OUTPUT_DIR = "output"
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
FPS = 24
SECONDS_PER_KEYFRAME = 3.0  # Each keyframe plays for 3 seconds


def main():
    parser = argparse.ArgumentParser(description="Animated Educational Video Generator")
    parser.add_argument("topic", help="Topic for the educational video")
    parser.add_argument(
        "--voice",
        choices=["female", "male", "casual"],
        default="female",
        help="TTS voice",
    )
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument(
        "--seconds", type=float, default=3.0, help="Seconds per keyframe"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    global FPS, SECONDS_PER_KEYFRAME
    FPS = args.fps
    SECONDS_PER_KEYFRAME = args.seconds

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    topic = args.topic
    run_id = f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(output_dir, exist_ok=True)

    logger.info("=" * 70)
    logger.info("Animated Educational Video Generator - A & B Style")
    logger.info("=" * 70)
    logger.info(f"Topic: {topic}")
    logger.info(f"FPS: {FPS}")
    logger.info(f"Seconds per keyframe: {SECONDS_PER_KEYFRAME}")
    logger.info(f"Resolution: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
    logger.info(f"Output: {output_dir}")
    logger.info("")

    # Step 1: Research
    logger.info("[STEP 1] Researching topic with Exa AI...")
    try:
        research_data = search(topic, num_results=8)
        logger.info(f"  Found {len(research_data)} sources")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        research_data = []
    logger.info("")

    # Step 2: Generate animated script with keyframes
    logger.info("[STEP 2] Generating animated script with 10 keyframes...")
    try:
        segments = generate_animated_script(topic, research_data)
        logger.info(f"  Generated {len(segments)} keyframe segments")
        for i, seg in enumerate(segments):
            logger.info(f"    Keyframe {i + 1}: {seg.get('narration', '')[:60]}...")
            logger.info(
                f"      A: {seg.get('A_position', '')}/{seg.get('A_expression', '')}, B: {seg.get('B_position', '')}/{seg.get('B_expression', '')}"
            )
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        # Fallback - create simple segments
        segments = [
            {
                "narration": f"Let me tell you about {topic}.",
                "keyframe_image": f"Introduction to {topic}",
                "A_position": "center-left",
                "A_expression": "curious",
                "B_position": "center-right",
                "B_expression": "curious",
            }
        ]
    logger.info("")

    # Save script
    import json

    script_path = os.path.join(output_dir, "script.json")
    with open(script_path, "w") as f:
        json.dump(segments, f, indent=2)
    logger.info(f"  Script saved: {script_path}")
    logger.info("")

    # Step 3: Generate keyframe images
    logger.info("[STEP 3] Generating keyframe images...")
    keyframe_paths = []
    for i, segment in enumerate(segments):
        keyframe_path = os.path.join(output_dir, f"keyframe_{i:02d}.png")
        generate_image_from_keyframe(segment, i + 1, keyframe_path, size="1920x1080")
        keyframe_paths.append(keyframe_path)
    logger.info(f"  Generated {len(keyframe_paths)} keyframe images")
    logger.info("")

    # Step 4: Interpolate frames (create animation)
    logger.info("[STEP 4] Interpolating frames (creating animation)...")
    frames_dir = os.path.join(output_dir, "frames")
    all_frames = generate_animation_sequence(
        keyframe_paths, frames_dir, fps=FPS, seconds_per_keyframe=SECONDS_PER_KEYFRAME
    )
    logger.info(f"  Generated {len(all_frames)} total frames")
    logger.info("")

    # Step 5: Generate audio for each segment
    logger.info("[STEP 5] Generating audio for each segment...")
    audio_segments = []
    total_duration = len(keyframe_paths) * SECONDS_PER_KEYFRAME
    frames_per_segment = int(FPS * SECONDS_PER_KEYFRAME)

    for i, segment in enumerate(segments):
        narration = segment.get("narration", "")
        audio_path = os.path.join(output_dir, f"audio_{i:02d}.mp3")

        # Calculate how many frames this audio should span
        start_frame = i * frames_per_segment
        end_frame = min((i + 1) * frames_per_segment, len(all_frames))

        logger.info(f"  Segment {i + 1}: {narration[:50]}...")
        asyncio.run(generate_speech_edge(narration, audio_path, args.voice))

        audio_segments.append(
            {"path": audio_path, "start_frame": start_frame, "end_frame": end_frame}
        )
    logger.info("")

    # Step 6: Combine frames into video
    logger.info("[STEP 6] Creating animated video...")
    raw_video_path = os.path.join(output_dir, "video_raw.mp4")
    create_video_from_frames(all_frames, raw_video_path, fps=FPS)
    logger.info("")

    # Step 7: Add audio to video
    logger.info("[STEP 7] Adding audio to video...")
    final_video_path = os.path.join(output_dir, "video.mp4")

    # Use ffmpeg to combine video and audio
    import subprocess

    # Build ffmpeg command
    inputs = ""
    for i, seg in enumerate(audio_segments):
        inputs += f"-i {seg['path']} "

    # For now, just use the first audio track (we can do segment-based audio later)
    cmd = f"ffmpeg -y -i {raw_video_path} -i {audio_segments[0]['path']} -c:v copy -c:a aac -shortest {final_video_path}"
    subprocess.run(cmd, shell=True, check=True)

    video_size = os.path.getsize(final_video_path) / (1024 * 1024)
    logger.info(f"  ✓ Final video saved: {final_video_path} ({video_size:.1f} MB)")

    logger.info("")
    logger.info("=" * 70)
    logger.info("DONE!")
    logger.info(f"  Script: {script_path}")
    logger.info(f"  Keyframes: {len(keyframe_paths)} images")
    logger.info(f"  Frames: {len(all_frames)} total")
    logger.info(f"  Video: {final_video_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
