# EduVideoGenerator

Create educational videos automatically with AI - 3Blue1Brown style!

## Features

- **Research**: Uses Exa AI to find relevant content on any topic
- **Script**: Kimi K2.5 generates educational scripts with embedded image prompts
- **Audio**: Edge TTS (free, high quality) converts script to speech
- **Images**: NanoGPT image generation (cartoon/math visualization style)
- **Video**: MoviePy combines everything with synced audio + images
- **Dark mode**: 3Blue1Brown-inspired aesthetic with neon colors

## Setup

```bash
pip install -r requirements.txt
```

## Configuration (.env)

```env
NANO_GPT_API_KEY=your_nano_gpt_key
NANO_GPT_BASE_URL=https://nano-gpt.com/api/v1
EXA_API_KEY=your_exa_key
```

Get free keys:
- NanoGPT: https://nano-gpt.com
- Exa AI: https://exa.ai

## Usage

```bash
# Basic usage (dark slides only - free)
python main.py "quantum computing"

# With AI-generated images (costs money)
python main.py "photosynthesis"

# Different voice
python main.py "world war 2" --voice male

# Use NanoGPT TTS instead of Edge TTS
python main.py "machine learning" --use-nano-tts
```

## How It Works

1. **Research**: Exa AI searches for educational content on your topic
2. **Script Generation**: Kimi K2.5 creates a script with `[IMAGE: description]` markers
3. **Parse**: Script is split into segments (text + image prompts)
4. **Audio**: Each segment gets its own audio file (Edge TTS)
5. **Images**: AI generates cartoon/math visualizations for each prompt
6. **Video**: All segments combined with synced audio + images

## Output

Generated videos saved to `output/` directory:
- `script.txt` - Full script
- `segment_XXX.mp3` - Audio for each segment
- `slide_XXX.png` - Generated images
- `video.mp4` - Final video

## Options

- `--voice [female|male|casual]` - TTS voice (default: female)
- `--no-images` - Skip image generation (use dark slides)
- `--use-nano-tts` - Use NanoGPT TTS instead of free Edge TTS

## Cost

- **Free**: Exa research, Edge TTS, dark slides
- **Paid**: NanoGPT image generation (~0.01-0.05 per image at 256x256)

## Example Topics

```bash
python main.py "how computers work"
python main.py "the solar system"
python main.py "how AI neural networks learn"
python main.py "blockchain technology explained"
```
