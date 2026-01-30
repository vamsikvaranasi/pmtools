"""
OpenRouter Image Generation Module
Pre-built module for Claude Code to call - handles session management,
multi-turn conversations, and output saving.
Uses OpenRouter API to access Gemini image generation models.
"""
import os
import json
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Try to load .env file, but don't fail if it's not accessible
try:
    load_dotenv()
except (PermissionError, IOError):
    # If .env file can't be read, continue - environment variables may be set elsewhere
    pass

from openai import OpenAI
from PIL import Image
import io

# Configuration
SESSION_FILE = ".image_session.json"
OUTPUT_DIR = "outputs"
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"
DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_RESOLUTION = "1K"

# Model constants
MODEL_NANO_BANANA = "google/gemini-2.5-flash-image-preview"
MODEL_NANO_BANANA_PRO = "google/gemini-3-pro-image-preview"


def _get_model_identifier(model_name: str) -> str:
    """
    Convert friendly model name to OpenRouter identifier.
    
    Args:
        model_name: Friendly name ("nano_banana", "nano_banana_pro") or full OpenRouter identifier
    
    Returns:
        OpenRouter model identifier string
    """
    model_map = {
        "nano_banana": MODEL_NANO_BANANA,
        "nano_banana_pro": MODEL_NANO_BANANA_PRO,
        "nano-banana": MODEL_NANO_BANANA,  # Backward compatibility
        "nano-banana-pro": MODEL_NANO_BANANA_PRO,  # Backward compatibility
    }
    
    # If it's a friendly name, map it
    if model_name.lower() in model_map:
        return model_map[model_name.lower()]
    
    # Otherwise, assume it's already a full identifier
    return model_name


def _get_client():
    """Initialize OpenRouter client"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment. Check your .env file.")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", ""),  # Optional
            "X-Title": os.environ.get("OPENROUTER_X_TITLE", ""),  # Optional
        }
    )


def _ensure_output_dir():
    """Create outputs directory if it doesn't exist"""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)


def _load_session():
    """Load existing session or return empty session"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"history": [], "outputs": [], "turn": 0}
    return {"history": [], "outputs": [], "turn": 0}


def _image_to_base64_data_url(image_path_or_obj):
    """Convert PIL Image or image path to base64 data URL"""
    if isinstance(image_path_or_obj, str):
        # It's a path - detect mime type from file extension
        image_path = image_path_or_obj.lower()
        if image_path.endswith(('.jpg', '.jpeg')):
            mime_type = "image/jpeg"
        elif image_path.endswith('.png'):
            mime_type = "image/png"
        elif image_path.endswith('.gif'):
            mime_type = "image/gif"
        elif image_path.endswith('.webp'):
            mime_type = "image/webp"
        else:
            # Try to detect from magic bytes
            with open(image_path_or_obj, 'rb') as f:
                header = f.read(12)
                if header[:2] == b'\xff\xd8':
                    mime_type = "image/jpeg"
                elif header[:8] == b'\x89PNG\r\n\x1a\n':
                    mime_type = "image/png"
                elif header[:6] in [b'GIF87a', b'GIF89a']:
                    mime_type = "image/gif"
                elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                    mime_type = "image/webp"
                else:
                    mime_type = "image/png"  # Default fallback
        
        with open(image_path_or_obj, 'rb') as f:
            image_data = f.read()
    else:
        # It's a PIL Image object
        buffer = io.BytesIO()
        # Try to preserve original format if available
        format_str = getattr(image_path_or_obj, 'format', 'PNG')
        if format_str:
            image_path_or_obj.save(buffer, format=format_str)
            if format_str.upper() == 'JPEG':
                mime_type = "image/jpeg"
            elif format_str.upper() == 'PNG':
                mime_type = "image/png"
            elif format_str.upper() == 'GIF':
                mime_type = "image/gif"
            elif format_str.upper() == 'WEBP':
                mime_type = "image/webp"
            else:
                mime_type = "image/png"
        else:
            image_path_or_obj.save(buffer, format='PNG')
            mime_type = "image/png"
        image_data = buffer.getvalue()
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def _reconstruct_history(raw_history):
    """
    Convert raw history dicts to OpenAI message format for OpenRouter API.
    Handles both text and image content.
    """
    messages = []
    for item in raw_history:
        role = item.get("role")
        parts = item.get("parts", [])
        
        # Build content array for this message
        content_parts = []
        
        for part_data in parts:
            if "text" in part_data:
                # Text part - OpenAI format uses {"type": "text", "text": "..."}
                content_parts.append({
                    "type": "text",
                    "text": part_data["text"]
                })
            elif "inline_data" in part_data:
                # Image part - convert to OpenAI format
                inline_data = part_data["inline_data"]
                mime_type = inline_data.get("mime_type", "image/png")
                image_data = base64.b64decode(inline_data["data"])
                
                # Convert to base64 data URL
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:{mime_type};base64,{base64_data}"
                
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                })
        
        # If we have content, add the message
        if content_parts:
            messages.append({
                "role": role,
                "content": content_parts if len(content_parts) > 1 else (content_parts[0]["text"] if len(content_parts) == 1 and content_parts[0]["type"] == "text" else content_parts)
            })
    
    return messages


def _save_session(session):
    """Save session to file"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(session, f)


def _get_next_output_path(session):
    """Generate next output filename"""
    _ensure_output_dir()
    turn = session.get("turn", 0) + 1
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{OUTPUT_DIR}/output_{turn:03d}_{timestamp}.png"


def new_session():
    """Clear the current session and start fresh"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    print("Session cleared. Ready for new image generation.")
    return {"history": [], "outputs": [], "turn": 0}


def session_info():
    """Display current session status"""
    session = _load_session()
    turn_count = session.get("turn", 0)
    outputs = session.get("outputs", [])

    if turn_count == 0:
        print("No active session. Start generating to create one.")
        return None

    print(f"Current session: {turn_count} turn(s)")
    print(f"Outputs generated:")
    for i, output in enumerate(outputs, 1):
        print(f"  {i}. {output}")

    return session


def revert(turns: int = 1):
    """
    Undo the last N turns from the current session.

    Args:
        turns: Number of turns to revert (default: 1)

    Returns:
        The updated session, or None if nothing to revert
    """
    session = _load_session()
    turn_count = session.get("turn", 0)

    if turn_count == 0:
        print("No active session to revert.")
        return None

    if turns > turn_count:
        print(f"Can only revert {turn_count} turn(s). Reverting all.")
        turns = turn_count

    # Each turn = 2 history items (user message + model response)
    items_to_remove = turns * 2
    session["history"] = session["history"][:-items_to_remove]

    # Remove outputs
    session["outputs"] = session["outputs"][:-turns]

    # Update turn count
    session["turn"] = turn_count - turns

    _save_session(session)

    if session["turn"] == 0:
        print(f"Reverted {turns} turn(s). Session is now empty.")
    else:
        print(f"Reverted {turns} turn(s). Now at turn {session['turn']}.")
        print(f"Last output: {session['outputs'][-1] if session['outputs'] else 'None'}")

    return session


def generate(
    prompt: str,
    reference_images: list = None,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    resolution: str = DEFAULT_RESOLUTION,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Generate or refine an image. Automatically continues existing session.

    Args:
        prompt: Text description of what to generate/change
        reference_images: Optional list of image paths to use as references
        aspect_ratio: "1:1", "3:4", "4:3", "16:9", "9:16", "21:9" (may be passed in prompt for some models)
        resolution: "1K", "2K", or "4K" (may be passed in prompt for some models)
        model: Friendly model name ("nano-banana", "nano-banana-pro") or full OpenRouter identifier

    Returns:
        Path to the generated image
    """
    # Convert friendly model name to identifier if needed
    model_identifier = _get_model_identifier(model)
    
    client = _get_client()
    session = _load_session()

    # Build messages array
    messages = []
    
    # Reconstruct existing history if continuing session
    if session["history"]:
        print(f"Continuing session (turn {session['turn'] + 1})...")
        messages = _reconstruct_history(session["history"])
    else:
        print("Starting new session...")

    # Build current user message content
    user_content = []
    
    # Add text prompt (use prompt as-is, image config handled via API parameter)
    user_content.append({
        "type": "text",
        "text": prompt
    })
    
    # Add reference images if provided
    if reference_images:
        for img_path in reference_images:
            if os.path.exists(img_path):
                data_url = _image_to_base64_data_url(img_path)
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                })
            else:
                print(f"Warning: Reference image not found: {img_path}")

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_content if len(user_content) > 1 else user_content[0]["text"]
    })

    # Make API call to OpenRouter
    try:
        # Build request parameters - OpenRouter uses extra_body for custom parameters
        extra_body = {
            "modalities": ["image", "text"]
        }
        
        # Add image_config if aspect_ratio or resolution differ from defaults
        if aspect_ratio != DEFAULT_ASPECT_RATIO or resolution != DEFAULT_RESOLUTION:
            extra_body["image_config"] = {
                "aspect_ratio": aspect_ratio,
                "image_size": resolution
            }
        
        response = client.chat.completions.create(
            model=model_identifier,
            messages=messages,
            extra_body=extra_body
        )
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        raise

    # Process response
    output_path = None
    response_parts = []
    
    # Extract response content
    if response.choices and len(response.choices) > 0:
        message = response.choices[0].message
        
        # According to OpenRouter docs, images are in message.images array
        # Check for images first (primary response format for image generation)
        if hasattr(message, 'images') and message.images:
            for image_obj in message.images:
                # Image format: {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
                if hasattr(image_obj, 'image_url') and hasattr(image_obj.image_url, 'url'):
                    image_url = image_obj.image_url.url
                elif isinstance(image_obj, dict) and image_obj.get("image_url", {}).get("url"):
                    image_url = image_obj["image_url"]["url"]
                else:
                    continue
                
                if image_url.startswith("data:"):
                    # Extract base64 data from data URL
                    header, encoded = image_url.split(",", 1)
                    try:
                        image_data = base64.b64decode(encoded)
                        output_path = _get_next_output_path(session)
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        print(f"Saved: {output_path}")
                        
                        # Extract mime type from data URL header
                        mime_type = "image/png"  # default
                        if ":" in header and ";" in header:
                            mime_type = header.split(":")[1].split(";")[0]
                        
                        # Store in session history
                        response_parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded
                            }
                        })
                    except Exception as e:
                        print(f"Error decoding image data: {e}")
        
        # Handle text content (if present)
        # Note: Images should come from message.images, but we handle text from message.content
        if message.content:
            if isinstance(message.content, str) and message.content.strip():
                # Text content from the model
                print(f"Model: {message.content}")
                response_parts.append({"text": message.content})
                    
            elif isinstance(message.content, list):
                # Content is a list of content parts
                for content_item in message.content:
                    if isinstance(content_item, dict):
                        if content_item.get("type") == "text":
                            text = content_item.get("text", "")
                            if text:
                                print(f"Model: {text}")
                                response_parts.append({"text": text})
                        elif content_item.get("type") == "image":
                            # Image data directly in response (OpenRouter format)
                            image_data_b64 = content_item.get("data", "")
                            if image_data_b64:
                                try:
                                    image_data = base64.b64decode(image_data_b64)
                                    output_path = _get_next_output_path(session)
                                    with open(output_path, 'wb') as f:
                                        f.write(image_data)
                                    print(f"Saved: {output_path}")
                                    
                                    # Determine mime type from magic bytes
                                    mime_type = "image/png"  # default
                                    if image_data[:2] == b'\xff\xd8':
                                        mime_type = "image/jpeg"
                                    elif image_data[:6] in [b'GIF87a', b'GIF89a']:
                                        mime_type = "image/gif"
                                    
                                    # Store in session history
                                    response_parts.append({
                                        "inline_data": {
                                            "mime_type": mime_type,
                                            "data": image_data_b64
                                        }
                                    })
                                except Exception as e:
                                    print(f"Error decoding image data: {e}")
                        elif content_item.get("type") == "image_url":
                            # Image in response - extract and save
                            image_url = content_item["image_url"]["url"]
                            if image_url.startswith("data:"):
                                # Base64 data URL
                                header, encoded = image_url.split(",", 1)
                                image_data = base64.b64decode(encoded)
                                output_path = _get_next_output_path(session)
                                with open(output_path, 'wb') as f:
                                    f.write(image_data)
                                print(f"Saved: {output_path}")
                                
                                # Extract mime type
                                mime_type = "image/png"  # default
                                if ":" in header and ";" in header:
                                    mime_type = header.split(":")[1].split(";")[0]
                                
                                # Store in session history
                                response_parts.append({
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": encoded
                                    }
                                })
    
    # If still no image found, log warning for debugging
    if not output_path and response.choices and len(response.choices) > 0:
        message = response.choices[0].message
        print("Warning: No image found in response.")
        print("Expected images in message.images array according to OpenRouter API.")
        if hasattr(message, 'images'):
            print(f"message.images exists: {message.images}")
        else:
            print("message.images attribute not found in response.")
        if message.content:
            print(f"Message content type: {type(message.content)}, length: {len(str(message.content))}")

    # Update session history
    # Store user message
    user_parts = [{"text": prompt}]
    if reference_images:
        for img_path in reference_images:
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                user_parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(img_data).decode('utf-8')
                    }
                })
    
    session["history"].append({"role": "user", "parts": user_parts})
    
    # Store model response
    session["history"].append({"role": "model", "parts": response_parts})
    session["turn"] = session.get("turn", 0) + 1
    if output_path:
        session["outputs"].append(output_path)

    _save_session(session)

    return output_path


# Convenience aliases
def gen(prompt, **kwargs):
    """Shorthand for generate()"""
    return generate(prompt, **kwargs)


if __name__ == "__main__":
    # Quick test
    print("Image Generation Module loaded.")
    print("Use: generate(prompt), new_session(), session_info(), revert()")
    print("")
    print("Functions:")
    print("  generate(prompt)     - Generate/refine an image")
    print("  new_session()        - Clear session, start fresh")
    print("  session_info()       - Show current session status")
    print("  revert(turns=1)      - Undo last N turns")
