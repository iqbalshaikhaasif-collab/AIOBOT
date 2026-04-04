"""
AgentX v2 — AI Layer
Pollinations.ai only. Free forever. No API key needed.
"""
import requests
import json
import re


def ask_ai(messages: list, timeout: int = 90) -> str:
    """
    Send messages to Pollinations.ai and get a response.
    messages: list of dicts like [{"role": "user", "content": "..."}]
    Returns the response text.
    """
    try:
        resp = requests.post(
            "https://text.pollinations.ai/openai/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "openai",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            # Fallback to legacy endpoint
            resp2 = requests.post(
                "https://text.pollinations.ai/",
                json={"messages": messages, "model": "openai"},
                timeout=timeout,
            )
            if resp2.status_code == 200:
                return resp2.text
            return None
    except Exception as e:
        print(f"[AI Error] {e}")
        return None


def chat(user_msg: str, system_msg: str = None, history: list = None) -> str:
    """
    Simple chat interface.
    user_msg: the user's message
    system_msg: optional system prompt
    history: optional list of {"role", "content"} dicts
    """
    messages = []
    if system_msg:
        messages.append({"role": "system", "content": system_msg})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_msg})

    result = ask_ai(messages)
    if result:
        return result
    return "Sorry, AI is temporarily unavailable. Please try again in a moment."


def extract_json(text: str):
    """Try to extract JSON from AI response."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try code blocks
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try raw JSON in text
    for pattern in [r"\[.*\]", r"\{.*\}"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    return None
