# Ollama Text Client Tool

A Python library and command-line interface for calling Ollama models directly for text-based interactions. Supports chat and generation endpoints, error handling, retry logic, and streaming responses.

## Features

- **Chat and Generation Endpoints**: Support for both chat mode (with conversation history) and generation mode (single prompt)
- **Error Handling**: Robust error handling with exponential backoff retry logic
- **Streaming Responses**: Optional streaming of responses as they're generated
- **Model Validation**: Checks if specified model exists locally before calling
- **Interactive Terminal Mode**: For testing purposes, provides interactive model and prompt selection
- **High Efficiency**: Optimized for general use with passed arguments

## Installation

```bash
cd /Users/vamsi/Workspaces/sortedsignals/tools/ollama-text-client
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

#### Basic Usage (Interactive)

Run without arguments for interactive mode:

```bash
python ollama_text_client.py
```

This will:
1. Display available models as a numbered list
2. Prompt for model selection
3. Prompt for input prompt

#### Direct Arguments

```bash
# With model and prompt arguments
python ollama_text_client.py --model mistral --prompt "Hello, world!"

# Chat mode
python ollama_text_client.py --model mistral --prompt "Tell me a joke" --chat

# Streaming response
python ollama_text_client.py --model mistral --prompt "Write a short story" --stream

# Custom API URL
python ollama_text_client.py --url http://localhost:11434 --model mistral --prompt "Hello"
```

#### All Options

```bash
python ollama_text_client.py --help
```

```
usage: ollama_text_client.py [-h] [-m MODEL] [-p PROMPT] [-c] [-s] [-u URL] [-t TIMEOUT]

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

### Library Usage

```python
from ollama_text_client import OllamaTextClient

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
    from ollama_text_client import print_streaming_response
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

## Configuration

### Default Settings

- **Base URL**: `http://localhost:11434` (can be overridden with `--url` parameter)
- **Timeout**: 60 seconds (can be overridden with `--timeout` parameter)
- **Max Retries**: 3 attempts with exponential backoff
- **Retry Delay**: Starts at 1 second and doubles with each retry

## Requirements

- Python 3.6+
- `requests` library

## Notes

- **Model Availability**: The tool will not automatically pull models from Ollama registry. If a model is not available locally, it will display an error with available models.
- **Streaming**: Streaming responses provide faster initial output but may be less efficient for small responses.
- **Error Handling**: The client includes retry logic for transient errors, with exponential backoff.

## Development

The tool is well-structured and includes:
- Comprehensive error handling
- Retry logic for failed requests
- Model validation before calling
- Interactive terminal mode for testing
- Streaming response support

## License

This tool is part of the Static and Sparks workspace.
