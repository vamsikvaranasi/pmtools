# Ollama Clients

A comprehensive Python library and command-line interface for calling Ollama models directly. Supports both text-based interactions (chat and generation) and image generation with local models like z-image and flux.

## Features

### Text Client
- **Chat and Generation Endpoints**: Support for both chat mode (with conversation history) and generation mode (single prompt)
- **Error Handling**: Robust error handling with exponential backoff retry logic
- **Streaming Responses**: Optional streaming of responses as they're generated
- **Model Validation**: Checks if specified model exists locally before calling
- **Interactive Terminal Mode**: For testing purposes, provides interactive model and prompt selection

### Image Client
- **Image Generation**: Generate images using local Ollama models (z-image, flux, etc.)
- **Interactive Aspect Ratio Selection**: Choose from preset ratios (1:1, 3:4, 4:3, 16:9, 9:16) in interactive mode
- **Progress Indicator**: Animated spinner shows generation progress with real-time feedback
- **Flexible Sizing**: Support for preset aspect ratios or custom dimensions (WIDTHxHEIGHT)
- **Advanced Parameters**: Control over denoising steps, random seed, and negative prompts
- **Automatic Saving**: Generated images are automatically saved with timestamped filenames
- **Model Selection**: Interactive model selection from available image generation models

> **Note**: Image generation functionality is currently only available on macOS systems. Support for other platforms is planned for future releases.

## Installation

```bash
cd ollama_clients
pip install -r requirements.txt
```

Or install directly:

```bash
pip install -e .
```

## Usage

### Text Client

#### Command-Line Interface

##### Basic Usage (Interactive)

Run without arguments for interactive mode:

```bash
python -m ollama_clients.text_client
```

This will:
1. Display available models as a numbered list
2. Prompt for model selection
3. Prompt for input prompt

##### Direct Arguments

```bash
# With model and prompt arguments
python -m ollama_clients.text_client --model mistral --prompt "Hello, world!"

# Chat mode
python -m ollama_clients.text_client --model mistral --prompt "Tell me a joke" --chat

# Streaming response
python -m ollama_clients.text_client --model mistral --prompt "Write a short story" --stream

# Custom API URL
python -m ollama_clients.text_client --url http://localhost:11434 --model mistral --prompt "Hello"
```

##### All Text Client Options

```bash
python -m ollama_clients.text_client --help
```

```
usage: text_client.py [-h] [-m MODEL] [-p PROMPT] [-c] [-s] [-u URL] [-t TIMEOUT]

Ollama Text Client - Interact with Ollama models from the command line

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        Model name to use (e.g., mistral, llama2)
  -p PROMPT, --prompt PROMPT
                        Prompt for the model
  -c, --chat            Use chat mode (interactive conversation)
  -s, --stream          Stream response as it's generated
  -u URL, --url URL     Ollama API base URL (default: http://localhost:11434)
  -t TIMEOUT, --timeout TIMEOUT
                        Request timeout in seconds (default: 60)
```

#### Library Usage

```python
from ollama_clients import OllamaTextClient

# Initialize client
client = OllamaTextClient()

# List available models
models = client.list_models()
print("Available models:", [m["name"] for m in models])

# Generation mode
response = client.generate(
    model="mistral",
    prompt="Write a Python function to calculate fibonacci numbers",
    stream=True
)

# Handle streaming response
if hasattr(response, 'iter_lines'):
    from ollama_clients.text_client import print_streaming_response
    print_streaming_response(response)
else:
    print(response.get("response"))

# Chat mode
response = client.chat(
    model="mistral",
    messages=[
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "What are its key features?"}
    ]
)

print(response.get("message", {}).get("content"))
```

### Image Client

#### Command-Line Interface

##### Basic Usage (Interactive)

Run without arguments for interactive mode:

```bash
python -m ollama_clients.image_client
```

This will:
1. Display available image generation models
2. Prompt for model selection
3. Prompt for image prompt
4. **Offer interactive aspect ratio selection** (1:1, 3:4, 4:3, 16:9, 9:16)
5. Optionally accept negative prompt
6. **Display animated progress indicator** during generation
7. Generate and save the image with timestamped filename

##### Direct Arguments

```bash
# Generate image with default settings
python -m ollama_clients.image_client --model "x/z-image-turbo" --prompt "A cute robot learning to paint"

# Custom size and output
python -m ollama_clients.image_client --model "x/z-image-turbo" --prompt "A sunset over mountains" --size 16:9 --output sunset.png

# With negative prompt and seed
python -m ollama_clients.image_client --model "flux" --prompt "A beautiful landscape" --negative "blurry, low quality" --seed 42

# Custom dimensions
python -m ollama_clients.image_client --model "x/z-image-turbo" --prompt "A portrait" --size 768x1024

# Specify output directory
python -m ollama_clients.image_client --prompt "A space scene" --output-dir ./my_images/
```

##### All Image Client Options

```bash
python -m ollama_clients.image_client --help
```

```
usage: image_client.py [-h] [-m MODEL] [-p PROMPT] [-s SIZE] [--steps STEPS] 
                       [--seed SEED] [-n NEGATIVE] [-o OUTPUT] [-u URL] 
                       [-d OUTPUT_DIR]

Ollama Image Client - Generate images using Ollama models from the command line

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        Model name to use (e.g., x/z-image-turbo, flux)
  -p PROMPT, --prompt PROMPT
                        Prompt for image generation
  -s SIZE, --size SIZE  Image size as WIDTHxHEIGHT or aspect ratio 
                        (1:1, 3:4, 4:3, 16:9, 9:16)
  --steps STEPS         Number of denoising steps (default: 20)
  --seed SEED           Random seed for reproducibility (optional)
  -n NEGATIVE, --negative NEGATIVE
                        Negative prompt to avoid certain features
  -o OUTPUT, --output OUTPUT
                        Output file path (default: auto-generated)
  -u URL, --url URL     Ollama API base URL (default: http://localhost:11434/v1/)
  -d OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory for generated images 
                        (default: ./generated_images/)
```

#### Library Usage

```python
from ollama_clients import OllamaImageClient

# Initialize client
client = OllamaImageClient()

# List available image models
models = client.list_image_models()
print("Available image models:", models)

# Generate and save image
output_path = client.generate_and_save(
    model="x/z-image-turbo",
    prompt="A cute robot learning to paint",
    size="1024x1024",
    steps=20,
    seed=42,
    negative_prompt="blurry, low quality",
    output_path="robot.png"
)

print(f"Image saved to: {output_path}")

# Generate image without saving (get base64)
response = client.generate(
    model="x/z-image-turbo",
    prompt="A sunset over mountains",
    size="16:9",
    steps=25
)

print(f"Image data: {response['image_data'][:50]}...")
```

## Aspect Ratios

The image client supports the following preset aspect ratios:

| Ratio | Dimensions |
|-------|-----------|
| 1:1   | 1024x1024 |
| 3:4   | 768x1024  |
| 4:3   | 1024x768  |
| 16:9  | 1456x819  |
| 9:16  | 819x1456  |

You can also specify custom dimensions using the format `WIDTHxHEIGHT` (e.g., `512x768`).

## Configuration

### Default Settings

#### Text Client
- **Base URL**: `http://localhost:11434` (can be overridden with `--url` parameter)
- **Timeout**: 60 seconds (can be overridden with `--timeout` parameter)
- **Max Retries**: 3 attempts with exponential backoff
- **Retry Delay**: Starts at 1 second and doubles with each retry

#### Image Client
- **Base URL**: `http://localhost:11434/v1/` (can be overridden with `--url` parameter)
- **Timeout**: 300 seconds (image generation can take longer)
- **Output Directory**: `./generated_images/` (can be overridden with `--output-dir` parameter)

## Requirements

- Python 3.6+
- `requests` library (for both text and image clients)
- macOS (for image generation functionality)

## Notes

- **Model Availability**: The tool will not automatically pull models from Ollama registry. If a model is not available locally, it will display an error with available models.
- **Streaming**: Streaming responses provide faster initial output but may be less efficient for small responses.
- **Error Handling**: The client includes retry logic for failed requests, with exponential backoff.
- **Image Generation**:
  - Image generation models like z-image and flux require Ollama to be running with the `/v1/` endpoint enabled
  - **Currently only supported on macOS systems**
  - Progress indicator provides real-time feedback during generation
  - Interactive mode automatically prompts for aspect ratio selection

## Development

The tool is well-structured and includes:
- Comprehensive error handling
- Retry logic for failed requests
- Model validation before calling
- Interactive terminal mode for testing
- Streaming response support (text client)
- Flexible image generation with multiple parameters
- Automatic image saving with timestamped filenames
- Animated progress indicators for long-running operations
- Thread-safe progress tracking
- Single dependency (`requests`) for both clients

## License

This tool is part of the Static and Sparks workspace.
