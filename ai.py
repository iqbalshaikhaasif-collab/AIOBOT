"""
ai.py — Pollinations.ai integration for AgentX Bot
FREE, no API key needed.
"""

import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are AgentX, an advanced AI assistant built into a Telegram bot. 
You are helpful, friendly, smart, and capable. You can help with coding, writing, math, 
analysis, creative tasks, and much more. Keep responses clear and well-structured.
Use markdown formatting when helpful. If asked about yourself, say you're AgentX.
IMPORTANT: Only respond with the actual helpful content. Never include metadata, 
JSON fields like "role" or "reasoningcontent" or "toolcalls" in your response."""


def _clean_response(text: str) -> str:
    """Clean up raw AI response - remove JSON metadata, reasoning, etc."""
    if not text:
        return text
    
    # If the response looks like raw JSON with metadata, extract just the useful content
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            # Check for various content fields
            content = data.get("content", "")
            if content:
                return _clean_response(content)
            
            # Check choices array (OpenAI format)
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                c = msg.get("content", "")
                if c:
                    return _clean_response(c)
            
            # If it has reasoningcontent but no clean content, skip it
            if "reasoningcontent" in data and "content" not in data:
                # This is metadata-only JSON, return nothing useful
                return ""
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Remove any JSON-like metadata that leaked into text
    # Pattern: {"role":"assistant","reasoningcontent":"...","toolcalls":}
    if re.match(r'^\s*\{.*"role"\s*:\s*"assistant".*\}$', text, re.DOTALL):
        try:
            data = json.loads(text)
            content = data.get("content", "")
            if content:
                return content.strip()
            # If only reasoning, try to extract a summary
            reasoning = data.get("reasoningcontent", "")
            if reasoning and len(reasoning) > 50:
                # The reasoning itself IS the useful content
                return reasoning.strip()
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Clean up any remaining JSON artifacts
    text = re.sub(r'\{?\s*"role"\s*:\s*"[^"]*"\s*,?\s*\}?', '', text)
    text = re.sub(r',?\s*"toolcalls"\s*:\s*\{\s*\}', '', text)
    text = re.sub(r',?\s*"reasoningcontent"\s*:\s*"[^"]*"', '', text)
    
    # Remove leading/trailing braces and commas from cleanup
    text = text.strip()
    text = re.sub(r'^[\s,\}]+', '', text)
    text = re.sub(r'[\s,\{]+$', '', text)
    
    return text.strip()


def chat(messages: list, max_retries: int = 3) -> str:
    """
    Send messages to Pollinations.ai and get a clean response.
    messages: list of dicts with 'role' and 'content'
    Returns: response string or error message
    """
    url = "https://text.pollinations.ai/"

    # Insert system prompt at the beginning
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    for attempt in range(max_retries):
        try:
            # Use POST with JSON body
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

            raw_text = response.text.strip()
            
            # Try to parse as structured JSON
            try:
                data = json.loads(raw_text)
                if isinstance(data, dict):
                    # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
                    if "choices" in data:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        if content:
                            cleaned = _clean_response(content)
                            if cleaned:
                                return cleaned
                    
                    # Direct format: {"content": "..."}
                    if "content" in data:
                        cleaned = _clean_response(data["content"])
                        if cleaned:
                            return cleaned
                    
                    # Has reasoning but we need to extract useful content
                    reasoning = data.get("reasoningcontent", "")
                    if reasoning and len(reasoning) > 50:
                        return reasoning.strip()
                    
                    # If none of the above worked, check if text representation is useful
                    text_repr = str(data)
                    if len(text_repr) > 200 and not text_repr.startswith("{'role':"):
                        return text_repr
                elif isinstance(data, str):
                    cleaned = _clean_response(data)
                    if cleaned:
                        return cleaned
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                pass

            # Not JSON — use raw text, but clean it
            if raw_text:
                cleaned = _clean_response(raw_text)
                if cleaned and len(cleaned) > 10:
                    return cleaned
                # If cleaning removed everything but original was long, return original
                if len(raw_text) > 50:
                    return raw_text

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
