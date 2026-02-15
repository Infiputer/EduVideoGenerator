import os
import sys
import logging
import asyncio
import argparse
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from moviepy import AudioFileClip

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
from src.interpolation import interpolate_frames, create_video_from_frames

load_dotenv()

OUTPUT_DIR = "output"
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
FPS = 24


def main():
    parser = argparse.ArgumentParser(description="Animated Educational Video Generator")
    parser.add_argument("topic", help="Topic for the educational video")
    parser.add_argument(
        "--voice",
        choices=["female", "male", "casual"],
        default="female",
        help="TTS voice",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

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
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
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

    # Step 3: Generate audio FIRST to get actual durations
    logger.info("[STEP 3] Generating audio for each segment...")
    audio_data = []
    for i, segment in enumerate(segments):
        audio_path = os.path.join(output_dir, f"audio_{i:02d}.mp3")
        logger.info(f"  Segment {i + 1}: {segment.get('narration', '')[:50]}...")
        asyncio.run(
            generate_speech_edge(segment.get("narration", ""), audio_path, args.voice)
        )

        # Get actual audio duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()

        audio_data.append(
            {"path": audio_path, "duration": duration, "segment": segment}
        )
        logger.info(f"    Audio duration: {duration:.1f}s")
    logger.info("")

    # Step 4: Generate keyframe images
    logger.info("[STEP 4] Generating keyframe images...")
    keyframe_paths = []
    for i, seg_data in enumerate(audio_data):
        segment = seg_data["segment"]
        keyframe_path = os.path.join(output_dir, f"keyframe_{i:02d}.png")
        generate_image_from_keyframe(segment, i + 1, keyframe_path, size="1920x1080")
        keyframe_paths.append(keyframe_path)
    logger.info(f"  Generated {len(keyframe_paths)} keyframe images")
    logger.info("")

    # Step 5: Interpolate frames with proper durations
    logger.info("[STEP 5] Interpolating frames (creating animation)...")
    all_frames = []
    frame_timestamps = []  # Track which frame ranges belong to which segment

    for i in range(len(audio_data) - 1):
        seg = audio_data[i]
        next_seg = audio_data[i + 1]
        duration = seg["duration"]

        # Calculate frames needed for this segment's duration
        frames_needed = int(duration * FPS)

        logger.info(f"  Segment {i + 1}: {duration:.1f}s = {frames_needed} frames")

        # Generate interpolated frames for this segment duration
        segment_interp_dir = os.path.join(output_dir, f"interp_{i}")
        os.makedirs(segment_interp_dir, exist_ok=True)
        frames = interpolate_frames(
            keyframe_paths[i],
            keyframe_paths[i + 1],
            segment_interp_dir,
            fps=FPS,
            duration_sec=duration,
        )

        # Only take the frames that fit this segment's audio
        segment_frames = frames[:frames_needed]
        all_frames.extend(segment_frames)

        # Add to last segment: extend final keyframe for its full duration
        if i == len(audio_data) - 2:
            final_duration = next_seg["duration"]
            final_frames_needed = int(final_duration * FPS)
            # Repeat last frame for remaining duration
            for _ in range(final_frames_needed):
                all_frames.append(keyframe_paths[-1])

    logger.info(f"  Generated {len(all_frames)} total frames")
    logger.info("")

    # Step 6: Create video from frames
    logger.info("[STEP 6] Creating animated video from frames...")
    raw_video_path = os.path.join(output_dir, "video_raw.mp4")
    create_video_from_frames(all_frames, raw_video_path, fps=FPS)
    logger.info("")

    # Step 7: Combine all audio into one file
    logger.info("[STEP 7] Combining audio...")
    audio_list_path = os.path.join(output_dir, "audio_list.txt")
    with open(audio_list_path, "w") as f:
        for ad in audio_data:
            f.write(f"file '{ad['path']}'\n")

    combined_audio_path = os.path.join(output_dir, "combined_audio.mp3")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            audio_list_path,
            "-c",
            "copy",
            combined_audio_path,
        ],
        capture_output=True,
    )

    # Step 8: Add audio to video
    logger.info("[STEP 8] Adding audio to video...")
    final_video_path = os.path.join(output_dir, "video.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            raw_video_path,
            "-i",
            combined_audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            final_video_path,
        ],
        capture_output=True,
    )

    video_size = os.path.getsize(final_video_path) / (1024 * 1024)
    logger.info(f"  ✓ Final video saved: {final_video_path} ({video_size:.1f} MB)")

    # Get video duration
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            final_video_path,
        ],
        capture_output=True,
        text=True,
    )
    duration = result.stdout.strip()
    logger.info(f"  Video duration: {duration} seconds")

    logger.info("")
    logger.info("=" * 70)
    logger.info("DONE!")
    logger.info(f"  Script: {script_path}")
    logger.info(f"  Video: {final_video_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
