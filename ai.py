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
IMPORTANT: Only respond with the actual helpful content. Never output raw JSON fields 
like "role", "reasoningcontent", "toolcalls" in your response. Only give the final answer."""


def _clean_response(text: str) -> str:
    """Clean up raw AI response — remove JSON metadata, reasoning artifacts."""
    if not text:
        return text

    # If it's JSON dict with metadata, extract the useful content
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            # Direct content field
            if "content" in data and isinstance(data["content"], str) and len(data["content"]) > 10:
                return _clean_response(data["content"])
            # OpenAI choices format
            if "choices" in data:
                content = data["choices"][0].get("message", {}).get("content", "")
                if content:
                    return _clean_response(content)
            # If only reasoning + metadata (no clean content), extract reasoning
            reasoning = data.get("reasoningcontent", "")
            if reasoning and len(reasoning) > 30:
                return reasoning.strip()
            return ""
    except (json.JSONDecodeError, TypeError):
        pass

    # Handle JSON embedded in text: {"role":"assistant","reasoningcontent":"...","toolcalls":{}}
    json_match = re.match(r'^\s*\{.*"role"\s*:\s*"assistant".*\}\s*$', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(text)
            content = data.get("content", "")
            if content:
                return content.strip()
            reasoning = data.get("reasoningcontent", "")
            if reasoning and len(reasoning) > 30:
                return reasoning.strip()
            return ""
        except (json.JSONDecodeError, TypeError):
            pass

    # Clean stray JSON artifacts from text
    text = re.sub(r'\{?\s*"role"\s*:\s*"[^"]*"\s*,?\s*\}?', '', text)
    text = re.sub(r',?\s*"toolcalls"\s*:\s*\{?\s*\}?\s*', '', text)
    text = re.sub(r',?\s*"reasoningcontent"\s*:\s*"[^"]*"\s*', '', text)
    text = text.strip()
    text = re.sub(r'^[\s,\}]+', '', text)
    text = re.sub(r'[\s,\{]+$', '', text)
    return text.strip() if len(text.strip()) > 10 else ""


def chat(messages: list, max_retries: int = 3) -> str:
    """Send messages to Pollinations.ai and get a clean response."""
    url = "https://text.pollinations.ai/"
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json={"messages": full_messages, "model": "openai", "seed": 42},
                timeout=60
            )
            response.raise_for_status()
            raw_text = response.text.strip()

            # Try structured JSON parsing
            try:
                data = json.loads(raw_text)
                if isinstance(data, dict):
                    if "choices" in data:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        if content:
                            cleaned = _clean_response(content)
                            if cleaned:
                                return cleaned
                    if "content" in data:
                        cleaned = _clean_response(data["content"])
                        if cleaned:
                            return cleaned
                    reasoning = data.get("reasoningcontent", "")
                    if reasoning and len(reasoning) > 30:
                        return reasoning.strip()
                elif isinstance(data, str):
                    cleaned = _clean_response(data)
                    if cleaned:
                        return cleaned
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                pass

            # Not JSON — use raw text cleaned
            cleaned = _clean_response(raw_text)
            if cleaned and len(cleaned) > 10:
                return cleaned
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
        messages = [{"role": "system", "content": system_prompt}] + messages
    return chat(messages)


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate an image URL from Pollinations.ai."""
    try:
        encoded = requests.utils.quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={42}&nologo=true"
    except Exception as e:
        logger.error(f"Image URL generation error: {e}")
        return ""
