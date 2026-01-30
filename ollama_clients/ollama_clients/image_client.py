#!/usr/bin/env python3
"""
Ollama Image Client Tool

A Python library and command-line interface for calling Ollama image generation models.
Supports image generation with customizable parameters like size, steps, seed, and negative prompts.

Author: Static and Sparks
Version: 1.0.0
"""

import argparse
import base64
import json
import os
import sys
import time
import requests
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

# Default configuration
DEFAULT_BASE_URL = "http://localhost:11434/v1/"
DEFAULT_TIMEOUT = 300  # Image generation can take longer
DEFAULT_OUTPUT_DIR = "./generated_images"

# Aspect ratio presets
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
    "16:9": (1456, 819),
    "9:16": (819, 1456),
}


class OllamaImageClient:
    """
    Client for interacting with Ollama API for image generation.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        output_dir: str = DEFAULT_OUTPUT_DIR,
    ):
        """
        Initialize Ollama image client.

        Args:
            base_url: Base URL of Ollama API (should include /v1/)
            timeout: Request timeout in seconds
            output_dir: Directory to save generated images
        """
        self.base_url = base_url
        self.timeout = timeout
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def list_image_models(self) -> List[str]:
        """
        List available image generation models.
        
        Returns:
            List of available image model names
        """
        try:
            # Get models from the API
            response = requests.get(
                urljoin(self.base_url, "models"),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            # Filter for image models
            image_models = [m["id"] for m in data.get("data", []) if any(
                keyword in m["id"].lower() for keyword in ['image', 'z-image', 'flux', 'dall-e']
            )]
            return image_models if image_models else ["x/z-image-turbo", "flux"]
        except Exception:
            # Return default image models if API call fails
            return ["x/z-image-turbo", "flux"]

    def generate(
        self,
        model: str,
        prompt: str,
        size: str = "1024x1024",
        steps: int = 20,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        show_progress: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate an image using the specified model.

        Args:
            model: Model name (e.g., 'x/z-image-turbo', 'flux')
            prompt: Text prompt for image generation
            size: Image size as "WIDTHxHEIGHT" (default: 1024x1024)
            steps: Number of denoising steps (default: 20)
            seed: Random seed for reproducibility (optional)
            negative_prompt: Negative prompt to avoid certain features (optional)
            show_progress: Show progress indicator during generation (optional)

        Returns:
            Response data with image information

        Raises:
            Exception: If request fails
        """
        # Progress indicator setup
        stop_progress = None
        progress_thread = None
        
        try:
            # Parse size
            if "x" in size.lower():
                width, height = map(int, size.lower().split("x"))
            else:
                width = height = 1024

            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "size": f"{width}x{height}",
                "response_format": "b64_json",
                "n": 1,
            }

            # Add optional parameters
            if seed is not None:
                payload["seed"] = seed
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            if steps:
                payload["steps"] = steps
            
            if show_progress:
                stop_progress = threading.Event()
                
                def show_progress_indicator():
                    chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    idx = 0
                    while not stop_progress.is_set():
                        print(f'\r{chars[idx % len(chars)]} Generating image...', end='', flush=True)
                        idx += 1
                        time.sleep(0.1)
                    print('\r✓ Image generated!     ', flush=True)
                
                progress_thread = threading.Thread(target=show_progress_indicator)
                progress_thread.start()

            try:
                # Make request
                response = requests.post(
                    urljoin(self.base_url, "images/generations"),
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract image data
                image_data = data.get("data", [{}])[0].get("b64_json", "")
                
                return {
                    "success": True,
                    "model": model,
                    "prompt": prompt,
                    "size": f"{width}x{height}",
                    "steps": steps,
                    "seed": seed,
                    "negative_prompt": negative_prompt,
                    "image_data": image_data,
                }
            finally:
                if show_progress and stop_progress and progress_thread:
                    stop_progress.set()
                    progress_thread.join()
                    
        except Exception as e:
            if show_progress and stop_progress and progress_thread:
                stop_progress.set()
                progress_thread.join()
            raise Exception(f"Image generation failed: {str(e)}")

    def generate_and_save(
        self,
        model: str,
        prompt: str,
        size: str = "1024x1024",
        steps: int = 20,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        show_progress: bool = False,
    ) -> str:
        """
        Generate an image and save it to a file.

        Args:
            model: Model name
            prompt: Text prompt for image generation
            size: Image size as "WIDTHxHEIGHT"
            steps: Number of denoising steps
            seed: Random seed for reproducibility
            negative_prompt: Negative prompt
            output_path: Custom output file path (optional)
            show_progress: Show progress indicator during generation (optional)

        Returns:
            Path to the saved image file
        """
        # Generate image
        response = self.generate(
            model=model,
            prompt=prompt,
            size=size,
            steps=steps,
            seed=seed,
            negative_prompt=negative_prompt,
            show_progress=show_progress,
        )

        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(" ", "_")
            output_path = os.path.join(self.output_dir, f"{timestamp}_{safe_prompt}.png")
        else:
            output_path = os.path.join(self.output_dir, output_path)

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save image
        image_data = response["image_data"]
        if isinstance(image_data, str):
            # It's base64 encoded
            image_bytes = base64.b64decode(image_data)
        else:
            # It's raw bytes
            image_bytes = image_data

        with open(output_path, "wb") as f:
            f.write(image_bytes)

        print(f"Image saved to: {output_path}")
        return output_path


def get_user_input(prompt: str = "", default: Optional[str] = None) -> str:
    """
    Get user input from terminal.

    Args:
        prompt: Prompt to display
        default: Default value if user presses enter

    Returns:
        User input string
    """
    try:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


def select_model_from_list(client: OllamaImageClient) -> str:
    """
    Display model selection menu and get user choice.

    Args:
        client: OllamaImageClient instance

    Returns:
        Selected model name
    """
    models = client.list_image_models()

    if not models:
        raise Exception("No image generation models available")

    print("\nAvailable image generation models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")

    while True:
        choice = get_user_input("Enter the number of the model you want to use: ")

        try:
            index = int(choice) - 1
            if 0 <= index < len(models):
                return models[index]
            print(f"Invalid selection. Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Invalid input. Please enter a number")


def select_aspect_ratio() -> tuple:
    """
    Display aspect ratio selection menu and get user choice.

    Returns:
        Tuple of (width, height)
    """
    print("\nAvailable aspect ratios:")
    ratios = list(ASPECT_RATIOS.keys())
    for i, ratio in enumerate(ratios, 1):
        width, height = ASPECT_RATIOS[ratio]
        print(f"{i}. {ratio} ({width}x{height})")

    while True:
        choice = get_user_input("Enter the number of the aspect ratio (or custom WIDTHxHEIGHT): ")

        try:
            index = int(choice) - 1
            if 0 <= index < len(ratios):
                return ASPECT_RATIOS[ratios[index]]
            print(f"Invalid selection. Please enter a number between 1 and {len(ratios)}")
        except ValueError:
            # Try to parse as custom size
            if "x" in choice.lower():
                try:
                    width, height = map(int, choice.lower().split("x"))
                    if width > 0 and height > 0:
                        return (width, height)
                except ValueError:
                    pass
            print("Invalid input. Please enter a number or custom size (e.g., 512x768)")


def main():
    """
    Main command-line interface for image generation.
    """
    parser = argparse.ArgumentParser(
        description="Ollama Image Client - Generate images using Ollama models from the command line"
    )
    parser.add_argument(
        "-m", "--model",
        help="Model name to use (e.g., x/z-image-turbo, flux)",
        default=None,
    )
    parser.add_argument(
        "-p", "--prompt",
        help="Prompt for image generation",
        default=None,
    )
    parser.add_argument(
        "-s", "--size",
        help="Image size as WIDTHxHEIGHT or aspect ratio (1:1, 3:4, 4:3, 16:9, 9:16)",
        default="1024x1024",
    )
    parser.add_argument(
        "--steps",
        type=int,
        help="Number of denoising steps (default: 20)",
        default=20,
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility (optional)",
        default=None,
    )
    parser.add_argument(
        "-n", "--negative",
        help="Negative prompt to avoid certain features",
        default=None,
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: auto-generated in ./generated_images/)",
        default=None,
    )
    parser.add_argument(
        "-u", "--url",
        help="Ollama API base URL (default: http://localhost:11434/v1/)",
        default=DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "-d", "--output-dir",
        help="Output directory for generated images (default: ./generated_images/)",
        default=DEFAULT_OUTPUT_DIR,
    )

    args = parser.parse_args()

    try:
        # Initialize client
        client = OllamaImageClient(
            base_url=args.url,
            output_dir=args.output_dir,
        )

        # Get model
        if args.model:
            model = args.model
        else:
            model = select_model_from_list(client)

        # Get prompt
        if args.prompt:
            prompt = args.prompt
        else:
            print("\nEnter your image prompt: ", end="")
            prompt = get_user_input()
            if not prompt:
                raise Exception("Prompt cannot be empty")

        # Get size - always ask in interactive mode if not provided via args
        if args.size == "1024x1024" and not args.prompt:
            # Interactive mode - ask user to select aspect ratio
            width, height = select_aspect_ratio()
            size = f"{width}x{height}"
        else:
            # Command-line mode or size was explicitly provided
            size = args.size
            if size.lower() in ASPECT_RATIOS:
                width, height = ASPECT_RATIOS[size.lower()]
                size = f"{width}x{height}"
            elif "x" not in size.lower():
                # Invalid size format
                raise Exception(f"Invalid size format: {size}. Use WIDTHxHEIGHT or aspect ratio (1:1, 3:4, 4:3, 16:9, 9:16)")

        # Get negative prompt if not provided
        negative_prompt = args.negative
        if not negative_prompt:
            neg_input = get_user_input("Enter negative prompt (optional, press Enter to skip): ", "")
            negative_prompt = neg_input if neg_input else None

        # Generate and save image
        print(f"\nGenerating image with model: {model}")
        print(f"Prompt: {prompt}")
        print(f"Size: {size}")
        if negative_prompt:
            print(f"Negative prompt: {negative_prompt}")
        print("-" * 50)
        print()  # Empty line before progress indicator

        output_path = client.generate_and_save(
            model=model,
            prompt=prompt,
            size=size,
            steps=args.steps,
            seed=args.seed,
            negative_prompt=negative_prompt,
            output_path=args.output,
            show_progress=True,  # Always show progress in CLI
        )

        print(f"Saved to: {output_path}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
