# Nano Banana Image Generator

A standalone, portable tool for generating images using OpenRouter's Gemini image generation models. Features both CLI and interactive modes, session management, prompt library, and support for multiple aspect ratios and models.

## Features

- 🎨 **Two Models**: Choose between Nano Banana (fast) or Nano Banana Pro (high quality)
- 📐 **Multiple Aspect Ratios**: 1:1, 3:4, 4:3, 16:9, 9:16, 21:9
- 💬 **Session Management**: Continue conversations and refine images across multiple turns
- 📚 **Prompt Library**: Save and reuse prompts from the `prompts/` directory
- 🖼️ **Reference Images**: Use multiple reference images to guide generation
- 🖥️ **Dual Interface**: CLI mode for automation, interactive mode for exploration

## Installation

1. **Clone or download this directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your OpenRouter API key:
     ```
     OPENROUTER_API_KEY=your_api_key_here
     ```
   - Get your API key from [OpenRouter](https://openrouter.ai/keys)

## Usage

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
python nano_banana.py
```

The interactive mode will guide you through:
1. Model selection (Nano Banana or Nano Banana Pro)
2. Aspect ratio selection
3. Session management (keep existing or start fresh)
4. Input images (optional, multiple images supported)
5. Prompt selection (from library or custom)
6. Confirmation and generation

### CLI Mode

Use command-line arguments for automation and scripting:

#### Basic Usage

```bash
# Single image with prompt
python nano_banana.py --model nano-banana-pro --prompt "A beautiful sunset over mountains"

# Use a prompt from the library
python nano_banana.py --model nano-banana-pro --prompt-file product-mockup.txt

# With reference images
python nano_banana.py --model nano-banana-pro --input-images img1.jpg img2.png --prompt "Create a design inspired by these images"
```

#### Advanced Usage

```bash
# Multiple images (space-separated)
python nano_banana.py \
  --model nano-banana-pro \
  --aspect-ratio 16:9 \
  --reset-session \
  --input-images img1.jpg img2.png img3.jpg img4.png \
  --prompt-file prompts/product-mockup.txt

# Multiple images (using multiple flags)
python nano_banana.py \
  --input-images img1.jpg \
  --input-images img2.png \
  --input-images img3.jpg \
  --prompt "Combine these images into a cohesive design"
```

### Command-Line Options

- `--model`: Model to use (`nano-banana` or `nano-banana-pro`, default: `nano-banana-pro`)
- `--aspect-ratio`: Aspect ratio (`1:1`, `3:4`, `4:3`, `16:9`, `9:16`, `21:9`, default: `1:1`)
- `--reset-session`: Clear existing session and start fresh
- `--input-images`: Reference image paths (can be used multiple times or space-separated)
- `--prompt`: Text prompt for image generation
- `--prompt-file`: Path to prompt file in `prompts/` directory (e.g., `product-mockup.txt`)

**Note**: Either `--prompt` or `--prompt-file` must be provided in CLI mode.

## Model Selection

### Nano Banana (`nano-banana`)
- Model: `google/gemini-3-image-preview`
- Faster generation
- Good for quick iterations and testing

### Nano Banana Pro (`nano-banana-pro`)
- Model: `google/gemini-3-pro-image-preview`
- Higher quality output
- Better for final production images
- Default model

## Aspect Ratios

- **1:1** - Square (Instagram posts, profile pictures)
- **3:4** - Portrait (mobile screens, vertical displays)
- **4:3** - Traditional photo format
- **16:9** - Widescreen (desktop wallpapers, presentations)
- **9:16** - Vertical video (stories, reels)
- **21:9** - Ultra-wide (cinematic, panoramic)

## Session Management

The tool automatically maintains a session across runs, allowing you to:
- Continue refining images in a conversation
- Build upon previous generations
- Maintain context across multiple turns

Use `--reset-session` in CLI mode or select "Start fresh session" in interactive mode to clear the session.

## Prompt Library

Store reusable prompts in the `prompts/` directory:

1. Create `.txt` or `.md` files with your prompts
2. Use descriptive filenames (e.g., `product-mockup.txt`)
3. Prompts automatically appear in interactive mode
4. Reference prompts in CLI mode with `--prompt-file`

Example:
```bash
# In interactive mode, select from the list
# In CLI mode:
python nano_banana.py --prompt-file product-mockup.txt
```

## Reference Images

You can provide multiple reference images to guide generation:

- **Interactive mode**: Enter paths separated by commas or spaces
- **CLI mode**: Space-separated list or multiple `--input-images` flags
- All images are validated before processing
- Supports common formats: JPG, PNG, GIF, WEBP

Example with many images:
```bash
python nano_banana.py \
  --input-images style1.jpg style2.jpg style3.jpg style4.jpg style5.jpg \
  --prompt "Create a design that combines the styles from these reference images"
```

## Output

Generated images are saved in the `outputs/` directory with the format:
```
outputs/output_001_HHMMSS.png
```

The tool displays the output path after generation.

## Project Structure

```
nano-banana-tool/
├── image_gen.py          # Core generation module
├── nano_banana.py        # Main CLI/interactive entry point
├── prompts/              # Prompt library directory
│   ├── README.md         # Instructions for adding prompts
│   ├── product-mockup.txt
│   ├── social-media-post.txt
│   └── ...               # Your custom prompts
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment file
├── README.md             # This file
└── outputs/              # Generated images (created on first run)
```

## Troubleshooting

### API Key Issues
- Ensure `.env` file exists and contains `OPENROUTER_API_KEY`
- Verify your API key is valid at [OpenRouter](https://openrouter.ai/keys)
- Check that the `.env` file is in the same directory as `nano_banana.py`

### Image Not Found
- Use absolute paths or paths relative to the current working directory
- Check file permissions
- Verify image file extensions are supported (JPG, PNG, GIF, WEBP)

### Session Issues
- Delete `.image_session.json` to reset the session manually
- Use `--reset-session` flag in CLI mode

## License

This tool is provided as-is for educational and personal use.
