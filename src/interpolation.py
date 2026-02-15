import os
import cv2
import numpy as np


def interpolate_frames(
    image1_path: str,
    image2_path: str,
    output_dir: str,
    fps: int = 24,
    duration_sec: float = 3.0,
) -> list:
    """
    Interpolate frames between two keyframe images using cross-fade.
    Simple but effective approach for cartoon animations.
    """
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)

    if img1 is None or img2 is None:
        raise ValueError(f"Could not load images")

    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    num_frames = int(fps * duration_sec)
    output_frames = []

    print(f"  Interpolating {num_frames} frames between keyframes...")

    for i in range(num_frames):
        t = i / (num_frames - 1) if num_frames > 1 else 0
        blend = t * t * (3 - 2 * t)

        blended = cv2.addWeighted(img1, 1 - blend, img2, blend, 0)

        zoom_factor = 1.0 + 0.02 * np.sin(t * np.pi)
        h, w = blended.shape[:2]

        if zoom_factor != 1.0:
            M = cv2.getRotationMatrix2D((w // 2, h // 2), 0, zoom_factor)
            blended = cv2.warpAffine(
                blended,
                M,
                (w, h),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(10, 10, 26),
            )

        frame_path = os.path.join(output_dir, f"frame_{i:04d}.png")
        cv2.imwrite(frame_path, blended)
        output_frames.append(frame_path)

    print(f"  ✓ Generated {len(output_frames)} interpolated frames")
    return output_frames


def generate_animation_sequence(
    keyframe_paths: list,
    output_dir: str,
    fps: int = 24,
    seconds_per_keyframe: float = 3.0,
) -> list:
    """Generate full animation sequence from keyframe images."""
    all_frames = []
    os.makedirs(output_dir, exist_ok=True)

    num_keyframes = len(keyframe_paths)

    for i in range(num_keyframes - 1):
        print(f"\n  Processing segment {i + 1}/{num_keyframes - 1}")
        start_img = keyframe_paths[i]
        end_img = keyframe_paths[i + 1]

        segment_dir = os.path.join(output_dir, f"segment_{i}")
        os.makedirs(segment_dir, exist_ok=True)

        frames = interpolate_frames(
            start_img, end_img, segment_dir, fps, seconds_per_keyframe
        )
        all_frames.extend(frames)

    return all_frames


def create_video_from_frames(frame_paths: list, output_path: str, fps: int = 24):
    """Create video from sequence of frames."""
    if not frame_paths:
        raise ValueError("No frames provided")

    first_frame = cv2.imread(frame_paths[0])
    if first_frame is None:
        raise ValueError(f"Could not read first frame: {frame_paths[0]}")

    height, width = first_frame.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        if frame is not None:
            out.write(frame)

    out.release()
    print(f"  ✓ Video saved: {output_path}")
    return output_path
