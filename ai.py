"""
ai.py — Pollinations.ai integration for AgentX Bot
FREE, no API key needed.
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are AgentX, an advanced AI assistant built into a Telegram bot. 
You are helpful, friendly, smart, and capable. You can help with coding, writing, math, 
analysis, creative tasks, and much more. Keep responses clear and well-structured.
Use markdown formatting when helpful. If asked about yourself, say you're AgentX."""


def chat(messages: list, max_retries: int = 3) -> str:
    """
    Send messages to Pollinations.ai and get a response.
    messages: list of dicts with 'role' and 'content'
    Returns: response string or error message
    """
    url = "https://text.pollinations.ai/"

    # Insert system prompt at the beginning
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json={
                    "messages": full_messages,
                    "model": "openai",
                    "seed": 42
                },
                timeout=60
            )
            response.raise_for_status()

            # Try to parse as JSON first
            try:
                data = response.json()
                if isinstance(data, dict):
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if text:
                        return text.strip()
                elif isinstance(data, str):
                    return data.strip()
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

            # Fall back to raw text
            text = response.text.strip()
            if text:
                return text

        except requests.exceptions.Timeout:
            logger.warning(f"Pollinations timeout, attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                return "⏰ AI is taking too long. Please try again."
        except requests.exceptions.ConnectionError:
            logger.warning(f"Pollinations connection error, attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                return "🌐 Can't reach AI server. Please try again in a moment."
        except Exception as e:
            logger.error(f"Pollinations error: {e}")
            if attempt == max_retries - 1:
                return "❌ AI service error. Please try again later."

    return "❌ Failed to get AI response after multiple attempts."


def chat_single(user_message: str, system_prompt: str = None) -> str:
    """Quick chat with a single message."""
    messages = [{"role": "user", "content": user_message}]
    if system_prompt:
        full_prompt = {"role": "system", "content": system_prompt}
        messages = [full_prompt] + messages
    return chat(messages)


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate an image URL from Pollinations.ai."""
    try:
        encoded = requests.utils.quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={42}&nologo=true"
    except Exception as e:
        logger.error(f"Image URL generation error: {e}")
        return ""
