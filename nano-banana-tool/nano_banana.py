#!/usr/bin/env python3
"""
Nano Banana Image Generator
Standalone CLI tool for generating images using OpenRouter's Gemini image models.
"""
import argparse
import os
import sys
from pathlib import Path
from image_gen import generate, new_session, session_info

# Aspect ratio options
ASPECT_RATIOS = {
    "1": "1:1",
    "2": "3:4",
    "3": "4:3",
    "4": "16:9",
    "5": "9:16",
    "6": "21:9",
}

# Model options
MODELS = {
    "1": ("nano-banana", "Nano Banana (google/gemini-2.5-flash-image-preview)"),
    "2": ("nano-banana-pro", "Nano Banana Pro (google/gemini-3-pro-image-preview)"),
}


def list_prompts():
    """Scan and display available prompts from prompts/ directory"""
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        return []
    
    prompt_files = []
    for ext in [".txt", ".md"]:
        prompt_files.extend(prompts_dir.glob(f"*{ext}"))
    
    return sorted(prompt_files)


def load_prompt(filename: str) -> str:
    """Load prompt from file (supports both .txt and .md)"""
    prompt_path = Path("prompts") / filename
    if not prompt_path.exists():
        # Try with .txt extension if not provided
        if not filename.endswith((".txt", ".md")):
            prompt_path = Path("prompts") / f"{filename}.txt"
            if not prompt_path.exists():
                prompt_path = Path("prompts") / f"{filename}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {filename}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def parse_image_paths(input_str: str) -> list[str]:
    """Parse comma or space-separated image paths"""
    if not input_str.strip():
        return []
    
    # Try comma-separated first
    if ',' in input_str:
        paths = [p.strip() for p in input_str.split(',')]
    else:
        # Space-separated
        paths = input_str.split()
    
    return [p for p in paths if p]  # Remove empty strings


def validate_images(image_paths: list[str]) -> list[str]:
    """Validate image files exist, return valid paths"""
    valid_paths = []
    for img_path in image_paths:
        path = Path(img_path)
        if path.exists() and path.is_file():
            valid_paths.append(str(path))
        else:
            print(f"Warning: Image not found: {img_path}")
    return valid_paths


def interactive_mode():
    """Main interactive flow"""
    print("\n" + "="*60)
    print("  Nano Banana Image Generator - Interactive Mode")
    print("="*60 + "\n")
    
    # 1. Model selection
    print("Select model:")
    for key, (_, description) in MODELS.items():
        print(f"  {key}. {description}")
    
    while True:
        model_choice = input("\nEnter choice (1-2) [default: 2]: ").strip() or "2"
        if model_choice in MODELS:
            model = MODELS[model_choice][0]
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    # 2. Aspect ratio selection
    print("\nSelect aspect ratio:")
    for key, ratio in ASPECT_RATIOS.items():
        print(f"  {key}. {ratio}")
    
    while True:
        ratio_choice = input("\nEnter choice (1-6) [default: 1]: ").strip() or "1"
        if ratio_choice in ASPECT_RATIOS:
            aspect_ratio = ASPECT_RATIOS[ratio_choice]
            break
        print("Invalid choice. Please enter 1-6.")
    
    # 3. Session management
    session = session_info()
    if session and session.get("turn", 0) > 0:
        print("\nSession management:")
        print("  1. Keep existing session (continue from previous generation)")
        print("  2. Start fresh session")
        while True:
            session_choice = input("\nEnter choice (1-2) [default: 1]: ").strip() or "1"
            if session_choice == "1":
                break
            elif session_choice == "2":
                new_session()
                break
            print("Invalid choice. Please enter 1 or 2.")
    else:
        print("\nNo existing session found. Starting fresh.")
    
    # 4. Input images
    print("\nInput images (optional):")
    print("Enter image paths (comma or space-separated, or press Enter to skip):")
    image_input = input("> ").strip()
    
    reference_images = []
    if image_input:
        image_paths = parse_image_paths(image_input)
        reference_images = validate_images(image_paths)
        if reference_images:
            print(f"\nUsing {len(reference_images)} reference image(s):")
            for img in reference_images:
                print(f"  - {img}")
        else:
            print("\nNo valid images found. Continuing without reference images.")
    
    # 5. Prompt selection
    prompts = list_prompts()
    prompt = None
    
    if prompts:
        print("\nPrompt selection:")
        print("  1. Use existing prompt from library")
        print("  2. Enter new prompt")
        
        while True:
            prompt_choice = input("\nEnter choice (1-2) [default: 2]: ").strip() or "2"
            if prompt_choice == "1":
                print("\nAvailable prompts:")
                for i, prompt_file in enumerate(prompts, 1):
                    print(f"  {i}. {prompt_file.name}")
                
                while True:
                    try:
                        prompt_num = input(f"\nSelect prompt (1-{len(prompts)}): ").strip()
                        if prompt_num:
                            idx = int(prompt_num) - 1
                            if 0 <= idx < len(prompts):
                                selected_file = prompts[idx]
                                prompt = load_prompt(selected_file.name)
                                print(f"\nLoaded prompt from: {selected_file.name}")
                                print(f"\nPrompt preview:\n{'-'*60}")
                                print(prompt[:200] + ("..." if len(prompt) > 200 else ""))
                                print("-"*60)
                                break
                            else:
                                print(f"Please enter a number between 1 and {len(prompts)}.")
                        else:
                            break
                    except ValueError:
                        print("Please enter a valid number.")
                    except FileNotFoundError as e:
                        print(f"Error: {e}")
                        break
                
                if prompt:
                    break
                # If no prompt selected, fall through to custom prompt
                print("\nFalling back to custom prompt entry...")
            
            if prompt_choice == "2" or not prompt:
                print("\nEnter your prompt:")
                prompt = input("> ").strip()
                if prompt:
                    break
                print("Prompt cannot be empty. Please enter a prompt.")
    else:
        print("\nNo prompts found in prompts/ directory.")
        print("Enter your prompt:")
        while True:
            prompt = input("> ").strip()
            if prompt:
                break
            print("Prompt cannot be empty. Please enter a prompt.")
    
    # 6. Confirmation
    print("\n" + "="*60)
    print("Configuration:")
    print(f"  Model: {MODELS[model_choice][1]}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Reference Images: {len(reference_images)}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print("="*60)
    
    confirm = input("\nGenerate image? (y/n) [default: y]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # 7. Generate
    print("\nGenerating image...\n")
    try:
        output_path = generate(
            prompt=prompt,
            reference_images=reference_images if reference_images else None,
            aspect_ratio=aspect_ratio,
            model=model
        )
        print(f"\n✓ Image generated successfully!")
        print(f"  Output: {output_path}")
    except Exception as e:
        print(f"\n✗ Error generating image: {e}")
        sys.exit(1)


def cli_mode(args):
    """Parse arguments and call generate"""
    # Handle session reset
    if args.reset_session:
        new_session()
    
    # Parse input images
    reference_images = []
    if args.input_images:
        # Flatten list if multiple --input-images flags were used
        all_images = []
        for img_list in args.input_images:
            if isinstance(img_list, list):
                all_images.extend(img_list)
            else:
                all_images.append(img_list)
        
        reference_images = validate_images(all_images)
        if reference_images and len(reference_images) != len(all_images):
            print(f"Warning: Only {len(reference_images)} of {len(all_images)} images were valid.")
    
    # Load prompt
    prompt = None
    if args.prompt_file:
        try:
            prompt = load_prompt(args.prompt_file)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.prompt:
        prompt = args.prompt
    else:
        print("Error: Either --prompt or --prompt-file must be provided.")
        sys.exit(1)
    
    # Validate aspect ratio
    if args.aspect_ratio not in ASPECT_RATIOS.values():
        print(f"Error: Invalid aspect ratio '{args.aspect_ratio}'.")
        print(f"Valid options: {', '.join(ASPECT_RATIOS.values())}")
        sys.exit(1)
    
    # Generate
    try:
        output_path = generate(
            prompt=prompt,
            reference_images=reference_images if reference_images else None,
            aspect_ratio=args.aspect_ratio,
            model=args.model
        )
        print(f"✓ Image generated: {output_path}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def main():
    """Entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Nano Banana Image Generator - Generate images using OpenRouter's Gemini models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (no arguments)
  python nano_banana.py

  # CLI mode with single image
  python nano_banana.py --model nano-banana-pro --input-images img1.jpg --prompt "A beautiful sunset"

  # CLI mode with multiple images
  python nano_banana.py --model nano-banana-pro --aspect-ratio 16:9 --input-images img1.jpg img2.png img3.jpg --prompt-file prompts/product-mockup.txt

  # Reset session and generate
  python nano_banana.py --reset-session --model nano-banana --prompt "A cat wearing sunglasses"
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="nano-banana-pro",
        help="Model to use: 'nano-banana' or 'nano-banana-pro' (default: nano-banana-pro)"
    )
    
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="1:1",
        choices=list(ASPECT_RATIOS.values()),
        help="Aspect ratio: 1:1, 3:4, 4:3, 16:9, 9:16, or 21:9 (default: 1:1)"
    )
    
    parser.add_argument(
        "--reset-session",
        action="store_true",
        help="Clear existing session and start fresh"
    )
    
    parser.add_argument(
        "--input-images",
        nargs="+",
        action="append",
        help="Reference image paths (can be used multiple times or space-separated)"
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        help="Text prompt for image generation"
    )
    
    parser.add_argument(
        "--prompt-file",
        type=str,
        help="Path to prompt file in prompts/ directory (e.g., 'product-mockup.txt')"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided (except help), run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        cli_mode(args)


if __name__ == "__main__":
    main()
