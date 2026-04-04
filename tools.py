"""
AgentX v2 — Tools
All bot features in one file.
"""
import requests
import re
import random
import string
import math
import json
from urllib.parse import urlparse


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEB SEARCH (DuckDuckGo — free, no key)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def web_search(query: str, max_results: int = 8) -> list:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            return results
    except Exception as e:
        print(f"[Search Error] {e}")
        return []


def search_and_summarize(query: str) -> str:
    """Search and use AI to summarize results."""
    results = web_search(query)
    if not results:
        return "No results found. Try different keywords."

    formatted = ""
    for i, r in enumerate(results, 1):
        formatted += f"{i}. {r['title']}\n   {r['snippet']}\n   {r['url']}\n\n"

    from ai import chat
    response = chat(
        f"Search query: {query}\n\nResults:\n{formatted}\n\nProvide a helpful summary of these results. Cite sources by number.",
        system_msg="You are a research assistant. Summarize search results clearly and cite sources."
    )
    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEB SCRAPING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def scrape_url(url: str) -> dict:
    """Scrape a URL and return title + text content."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        # Try to extract text from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = soup.title.string if soup.title else ""
        text = soup.get_text(separator="\n", strip=True)
        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return {"title": title or url, "text": text[:15000], "url": url}
    except Exception as e:
        return {"error": str(e)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGE GENERATION (Pollinations.ai — free)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_image(prompt: str) -> str:
    """Generate an image using Pollinations.ai. Returns URL."""
    try:
        clean = prompt.strip().replace(" ", ",")
        url = f"https://image.pollinations.ai/prompt/{clean}?width=1024&height=1024&nologo=true"
        return url
    except Exception as e:
        print(f"[Image Gen Error] {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FLASHCARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_flashcards(topic: str) -> list:
    """Generate flashcards using AI."""
    from ai import chat, extract_json
    response = chat(
        f"Create 5 flashcards about: {topic}",
        system_msg='You MUST respond with ONLY a valid JSON array. Each item must have "front" (question) and "back" (answer). No other text.'
    )
    cards = extract_json(response)
    if cards and isinstance(cards, list):
        return cards[:10]
    return []


def format_flashcards(cards: list) -> str:
    text = "Flashcards:\n\n"
    for i, c in enumerate(cards, 1):
        text += f"Card {i}:\n  Q: {c.get('front', '?')}\n  A: {c.get('back', '?')}\n\n"
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUIZ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_quiz(topic: str) -> list:
    """Generate a multiple choice quiz using AI."""
    from ai import chat, extract_json
    response = chat(
        f"Create 5 multiple choice questions about: {topic}",
        system_msg='You MUST respond with ONLY a valid JSON array. Each item must have "question", "options" (array of 4 strings), and "correct" (the correct answer string). No other text.'
    )
    questions = extract_json(response)
    if questions and isinstance(questions, list):
        return questions[:10]
    return []


def format_quiz(questions: list) -> str:
    text = ""
    for i, q in enumerate(questions, 1):
        text += f"Q{i}: {q.get('question', '?')}\n"
        opts = q.get("options", [])
        for j, opt in enumerate(opts):
            marker = " *" if opt == q.get("correct", "") else ""
            text += f"  {chr(65+j)}) {opt}{marker}\n"
        text += "\n"
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSLATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def translate(text: str, to_lang: str = "English") -> str:
    """Translate text to specified language using AI."""
    from ai import chat
    return chat(
        f"Translate the following text to {to_lang}. Only output the translation, nothing else:\n\n{text}",
        system_msg="You are a professional translator. Provide accurate translations."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALCULATOR / MATH SOLVER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calc(expression: str) -> str:
    """Solve math problems using AI."""
    from ai import chat
    # Try simple Python eval first for basic arithmetic
    safe = expression.replace("^", "**").strip()
    allowed = set("0123456789+-*/.() ")
    if all(c in allowed for c in safe) and safe:
        try:
            result = eval(safe, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
        except Exception:
            pass

    return chat(
        f"Solve this math problem step by step: {expression}",
        system_msg="You are a math expert. Show step-by-step solution. End with the final answer clearly."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEFINE WORD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def define(word: str) -> str:
    """Get definition of a word using AI."""
    from ai import chat
    return chat(
        f"Define the word/phrase: {word}",
        system_msg="Provide: 1) Definition 2) Part of speech 3) Example sentence 4) Synonyms 5) Etymology if known. Be concise."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASSWORD GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def gen_password(length: int = 16, special: bool = True) -> str:
    """Generate a secure random password."""
    chars = string.ascii_letters + string.digits
    if special:
        chars += "!@#$%^&*_+-=?"
    return "".join(random.choice(chars) for _ in range(length))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JOKE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def random_joke() -> str:
    """Get a random joke."""
    try:
        resp = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5)
        if resp.status_code == 200:
            j = resp.json()
            return f"{j['setup']}\n\n{j['punchline']}"
    except Exception:
        pass
    from ai import chat
    return chat("Tell me a funny joke. Just the joke, no intro.", system_msg="You are a comedian.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUOTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def random_quote() -> str:
    """Get an inspirational quote."""
    try:
        resp = requests.get("https://api.quotable.io/random", timeout=5)
        if resp.status_code == 200:
            q = resp.json()
            return f'"{q["content"]}"\n\n— {q["author"]}'
    except Exception:
        pass
    from ai import chat
    return chat("Give me one inspirational quote with its author. Nothing else.", system_msg="You are inspirational.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RANDOM FACT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def random_fact() -> str:
    """Get a random interesting fact."""
    try:
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout=5)
        if resp.status_code == 200:
            return resp.json()["text"]
    except Exception:
        pass
    from ai import chat
    return chat("Tell me one really interesting and surprising fact. Just the fact, no intro.", system_msg="You are a trivia expert.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REWRITE TEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def rewrite_text(text: str, style: str = "better") -> str:
    """Rewrite text in a different style."""
    styles = {
        "professional": "professional and formal",
        "casual": "casual and friendly",
        "academic": "academic and scholarly",
        "simple": "simple, easy to understand for a 10 year old",
        "creative": "creative and engaging",
    }
    desc = styles.get(style.lower(), style)
    from ai import chat
    return chat(
        f"Rewrite this text to sound more {desc}:\n\n{text}",
        system_msg="You are an expert writer. Rewrite the text maintaining the same meaning but improving the style as requested. Only output the rewritten text."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARIZE TEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def summarize_text(text: str) -> str:
    """Summarize a block of text."""
    from ai import chat
    return chat(
        f"Summarize this text concisely:\n\n{text[:8000]}",
        system_msg="Provide a clear, concise summary. Use bullet points for key points."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPARE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compare_things(a: str, b: str) -> str:
    """Compare two things using AI."""
    from ai import chat
    return chat(
        f"Compare {a} vs {b}",
        system_msg="Provide a structured comparison: similarities, differences, pros/cons, and a recommendation. Use tables or bullet points."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_urls(text: str) -> list:
    return re.findall(r"https?://[^\s<>)\"]+", text)

def word_count(text: str) -> dict:
    words = text.split()
    chars = len(text)
    sentences = text.count(".") + text.count("!") + text.count("?")
    return {
        "words": len(words),
        "characters": chars,
        "sentences": max(sentences, 1),
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
    }

def split_text(text: str, max_len: int = 4000) -> list:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        bp = text.rfind("\n\n", 0, max_len)
        if bp == -1:
            bp = text.rfind("\n", 0, max_len)
        if bp == -1:
            bp = max_len
        chunks.append(text[:bp])
        text = text[bp:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks
