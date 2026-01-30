#!/usr/bin/env python3
"""
Ollama Client Tool

A Python library and command-line interface for calling Ollama models directly.
Supports chat and generation endpoints, error handling, retry logic, and streaming responses.

Author: Static and Sparks
Version: 1.0.0
"""

import argparse
import json
import requests
import sys
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

# Default configuration
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


class OllamaTextClient:
    """
    Client for interacting with Ollama API for text-based interactions.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize Ollama text client.

        Args:
            base_url: Base URL of Ollama API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        stream: bool = False,
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Make a request to Ollama API with retry logic.

        Args:
            endpoint: API endpoint
            data: Request payload
            stream: Whether to stream response

        Returns:
            Response data or streaming response object

        Raises:
            Exception: If request fails after all retries
        """
        url = urljoin(self.base_url, endpoint)
        headers = {"Content-Type": "application/json"}

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout,
                    stream=stream,
                )

                if response.status_code == 200:
                    if stream:
                        return response
                    return response.json()
                elif response.status_code == 404:
                    raise Exception("Model not found. Please check if the model exists locally.")
                elif response.status_code == 500:
                    raise Exception("Ollama server error")
                else:
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

        raise Exception("Request failed")

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Ollama models.

        Returns:
            List of available models with details

        Raises:
            Exception: If request fails
        """
        try:
            response = requests.get(
                urljoin(self.base_url, "/api/tags"),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list models: {str(e)}")

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Generate a completion from a model.

        Args:
            model: Model name
            prompt: Prompt text
            system: System prompt (optional)
            template: Prompt template (optional)
            context: Context from previous conversation (optional)
            stream: Whether to stream response
            options: Model options (optional)

        Returns:
            Generated completion or streaming response

        Raises:
            Exception: If model not available or request fails
        """
        # Check if model is available
        available_models = [m["name"] for m in self.list_models()]
        if model not in available_models:
            raise Exception(
                f"Model '{model}' not available. Available models: {', '.join(available_models)}"
            )

        data: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }

        if system:
            data["system"] = system
        if template:
            data["template"] = template
        if context:
            data["context"] = context
        if options:
            data["options"] = options

        return self._make_request("/api/generate", data, stream=stream)

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Chat with a model using conversation history.

        Args:
            model: Model name
            messages: List of messages (each with 'role' and 'content')
            stream: Whether to stream response
            options: Model options (optional)

        Returns:
            Chat response or streaming response

        Raises:
            Exception: If model not available or request fails
        """
        # Check if model is available
        available_models = [m["name"] for m in self.list_models()]
        if model not in available_models:
            raise Exception(
                f"Model '{model}' not available. Available models: {', '.join(available_models)}"
            )

        data: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if options:
            data["options"] = options

        return self._make_request("/api/chat", data, stream=stream)

    def pull_model(self, model: str, stream: bool = False) -> Union[Dict[str, Any], requests.Response]:
        """
        Pull a model from Ollama registry (not recommended for production).

        Args:
            model: Model name
            stream: Whether to stream response

        Returns:
            Pull response or streaming response

        Raises:
            Exception: If request fails
        """
        data = {
            "name": model,
            "stream": stream,
        }
        return self._make_request("/api/pull", data, stream=stream)


def print_streaming_response(response: requests.Response) -> Dict[str, Any]:
    """
    Print streaming response and collect final result.

    Args:
        response: Streaming response object

    Returns:
        Final response data
    """
    final_data = {}
    full_response = ""

    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                final_data = data

                if "response" in data:
                    print(data["response"], end="", flush=True)
                    full_response += data["response"]

                if "error" in data:
                    print(f"\nError: {data['error']}")
                    break

            except json.JSONDecodeError as e:
                print(f"\nError decoding response: {e}")
                break

    print()
    return final_data


def get_user_input() -> str:
    """
    Get user input from terminal.

    Returns:
        User input string
    """
    try:
        return input().strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


def select_model_from_list(client: OllamaTextClient) -> str:
    """
    Display model selection menu and get user choice.

    Args:
        client: OllamaClient instance

    Returns:
        Selected model name

    Raises:
        Exception: If no models available or invalid selection
    """
    models = client.list_models()

    if not models:
        raise Exception("No Ollama models available locally")

    print("Available models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']} ({model.get('size', 'unknown')} bytes)")

    while True:
        print("\nEnter the number of the model you want to use: ", end="")
        choice = get_user_input()

        try:
            index = int(choice) - 1
            if 0 <= index < len(models):
                return models[index]["name"]
            print(f"Invalid selection. Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Invalid input. Please enter a number")


def main():
    """
    Main command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="Ollama Text Client - Interact with Ollama models from the command line for text-based interactions"
    )
    parser.add_argument(
        "-m", "--model",
        help="Model name to use (e.g., mistral, llama2)",
        default=None,
    )
    parser.add_argument(
        "-p", "--prompt",
        help="Prompt for the model",
        default=None,
    )
    parser.add_argument(
        "-c", "--chat",
        action="store_true",
        help="Use chat mode (interactive conversation)",
    )
    parser.add_argument(
        "-s", "--stream",
        action="store_true",
        help="Stream response as it's generated",
    )
    parser.add_argument(
        "-u", "--url",
        help="Ollama API base URL (default: http://localhost:11434)",
        default=DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        help="Request timeout in seconds (default: 60)",
        default=DEFAULT_TIMEOUT,
    )

    args = parser.parse_args()

    try:
        # Initialize client
        client = OllamaTextClient(
            base_url=args.url,
            timeout=args.timeout,
        )

        # Get model
        if args.model:
            model = args.model
            # Verify model exists
            available_models = [m["name"] for m in client.list_models()]
            if model not in available_models:
                raise Exception(
                    f"Model '{model}' not available. Available models: {', '.join(available_models)}"
                )
        else:
            model = select_model_from_list(client)

        # Get prompt
        if args.prompt:
            prompt = args.prompt
        else:
            print("\nEnter your prompt: ", end="")
            prompt = get_user_input()
            if not prompt:
                raise Exception("Prompt cannot be empty")

        if args.chat:
            # Chat mode
            messages = [
                {"role": "user", "content": prompt},
            ]
            print(f"\nUsing model: {model}")
            print("-" * 50)

            if args.stream:
                response = client.chat(model, messages, stream=True)
                print_streaming_response(response)
            else:
                response = client.chat(model, messages, stream=False)
                print(response.get("message", {}).get("content", "No response"))

        else:
            # Generation mode
            print(f"\nUsing model: {model}")
            print("-" * 50)

            if args.stream:
                response = client.generate(model, prompt, stream=True)
                print_streaming_response(response)
            else:
                response = client.generate(model, prompt, stream=False)
                print(response.get("response", "No response"))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
