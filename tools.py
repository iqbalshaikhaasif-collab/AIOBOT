"""
tools.py — All feature implementations for AgentX Bot
70 features: AI-powered + pure Python utilities.
"""

import random
import string
import hashlib
import base64
import re
import math
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from ai import chat_single, generate_image

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
# SECTION 1: SEARCH & WEB TOOLS
# ═══════════════════════════════════════════════════

def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "🔍 No results found."
        text = f"🔍 *Search results for: {query}*\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "")[:150]
            href = r.get("href", "")
            text += f"*{i}.* {title}\n{body}\n🔗 {href}\n\n"
        return text
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"❌ Search failed: {str(e)[:100]}"


def search_news(query: str) -> str:
    """Search for news."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=5))
        if not results:
            return "📰 No news found."
        text = f"📰 *News about: {query}*\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "")[:150]
            source = r.get("source", "")
            text += f"*{i}.* {title}\n{body}\n📌 {source}\n\n"
        return text
    except Exception as e:
        logger.error(f"News search error: {e}")
        return f"❌ News search failed: {str(e)[:100]}"


def summarize_url(url: str) -> str:
    """Summarize content from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)[:3000]

        if not text or len(text) < 50:
            return "❌ Could not extract useful content from that URL."

        prompt = f"Summarize the following web page content in clear bullet points. Keep it concise but informative:\n\n{text}"
        summary = chat_single(prompt, "You are a helpful summarizer. Use bullet points.")
        return f"📋 *Summary of {url}*\n\n{summary}"
    except requests.exceptions.Timeout:
        return "⏰ URL took too long to load."
    except Exception as e:
        return f"❌ Could not process URL: {str(e)[:100]}"


# ═══════════════════════════════════════════════════
# SECTION 2: AI-POWERED TOOLS
# ═══════════════════════════════════════════════════

def gen_image(prompt: str) -> str:
    """Generate an AI image."""
    try:
        url = generate_image(prompt)
        if url:
            return f"🖼️ *Generating image...*\n\n{url}\n\n⏳ Image will appear above once loaded!"
        return "❌ Failed to generate image URL."
    except Exception as e:
        return f"❌ Image generation failed: {str(e)[:100]}"


def gen_code(description: str) -> str:
    """Generate code from description."""
    try:
        prompt = f"Write clean, well-commented code for: {description}\n\nProvide the code in a code block with the appropriate language specified."
        result = chat_single(prompt, "You are an expert programmer. Always provide code in markdown code blocks with language specified. Explain briefly after the code.")
        return f"💻 *Code for: {description}*\n\n{result}"
    except Exception as e:
        return f"❌ Code generation failed: {str(e)[:100]}"


def debug_code(code: str) -> str:
    """Debug code."""
    try:
        prompt = f"Find and fix bugs in this code. Explain each issue and provide the corrected version:\n\n{code}"
        result = chat_single(prompt, "You are an expert debugger. Identify all bugs, explain them, and provide corrected code in markdown code blocks.")
        return f"🔧 *Debug Results*\n\n{result}"
    except Exception as e:
        return f"❌ Debug failed: {str(e)[:100]}"


def explain_code(code: str) -> str:
    """Explain code."""
    try:
        prompt = f"Explain this code step by step in simple terms:\n\n{code}"
        result = chat_single(prompt, "You are a patient coding teacher. Explain code line by line in simple, clear language that a beginner can understand.")
        return f"📖 *Code Explanation*\n\n{result}"
    except Exception as e:
        return f"❌ Explanation failed: {str(e)[:100]}"


def gen_flashcards(topic: str) -> str:
    """Generate flashcards on a topic."""
    try:
        prompt = f"Create 5 flashcards about {topic}. Format each as:\nFRONT: [question/term]\nBACK: [answer/definition]\n\nMake them educational and clear."
        result = chat_single(prompt, "You are an educational flashcard creator. Always use the exact format FRONT:/BACK: for each card.")
        return f"📚 *Flashcards: {topic}*\n\n{result}"
    except Exception as e:
        return f"❌ Flashcard generation failed: {str(e)[:100]}"


def gen_quiz(topic: str) -> str:
    """Generate a quiz."""
    try:
        prompt = f"Create a 5-question multiple choice quiz about {topic}. Format:\nQ1. [question]\na) ...\nb) ...\nc) ...\nd) ...\nAnswer: [correct letter]\n\nAfter all questions, provide the answer key at the bottom."
        result = chat_single(prompt, "You are a quiz creator. Always provide the answer key at the very end.")
        return f"📝 *Quiz: {topic}*\n\n{result}"
    except Exception as e:
        return f"❌ Quiz generation failed: {str(e)[:100]}"


def translate_text(text: str, target_lang: str = "Spanish") -> str:
    """Translate text."""
    try:
        prompt = f"Translate the following text to {target_lang}. Only provide the translation, nothing else:\n\n{text}"
        result = chat_single(prompt, "You are a professional translator. Only output the translation.")
        return f"🌐 *Translation ({target_lang})*\n\n{result}"
    except Exception as e:
        return f"❌ Translation failed: {str(e)[:100]}"


def rewrite_text(text: str, style: str = "better") -> str:
    """Rewrite text in a different style."""
    try:
        prompt = f"Rewrite the following text to make it {style}:\n\n{text}"
        result = chat_single(prompt, "You are a skilled writer. Rewrite text as requested.")
        return f"✍️ *Rewritten ({style})*\n\n{result}"
    except Exception as e:
        return f"❌ Rewrite failed: {str(e)[:100]}"


def compare_things(item1: str, item2: str) -> str:
    """Compare two things."""
    try:
        prompt = f"Compare {item1} and {item2}. Provide pros, cons, and a summary of when to use each."
        result = chat_single(prompt, "You are an analytical comparison expert. Provide balanced pros/cons.")
        return f"⚖️ *Comparison: {item1} vs {item2}*\n\n{result}"
    except Exception as e:
        return f"❌ Comparison failed: {str(e)[:100]}"


def summarize_text(text: str) -> str:
    """Summarize text."""
    try:
        prompt = f"Summarize the following text concisely in bullet points:\n\n{text}"
        result = chat_single(prompt, "You are a concise summarizer. Use bullet points.")
        return f"📋 *Summary*\n\n{result}"
    except Exception as e:
        return f"❌ Summarization failed: {str(e)[:100]}"


def gen_story(topic: str) -> str:
    """Generate a story."""
    try:
        prompt = f"Write a creative short story about: {topic}\n\nMake it engaging, with a clear beginning, middle, and end. Keep it under 500 words."
        result = chat_single(prompt, "You are a creative fiction writer. Write engaging short stories.")
        return f"📖 *Story: {topic}*\n\n{result}"
    except Exception as e:
        return f"❌ Story generation failed: {str(e)[:100]}"


def gen_poem(topic: str) -> str:
    """Generate a poem."""
    try:
        prompt = f"Write a beautiful poem about: {topic}\n\nMake it lyrical and expressive."
        result = chat_single(prompt, "You are a talented poet. Write beautiful, expressive poems.")
        return f"🎵 *Poem: {topic}*\n\n{result}"
    except Exception as e:
        return f"❌ Poem generation failed: {str(e)[:100]}"


def solve_math(equation: str) -> str:
    """Solve a math equation/problem."""
    try:
        prompt = f"Solve this math problem step by step: {equation}\n\nShow all your work clearly."
        result = chat_single(prompt, "You are a math tutor. Show step-by-step solutions clearly.")
        return f"🔢 *Math Solution*\n\n{result}"
    except Exception as e:
        return f"❌ Math solving failed: {str(e)[:100]}"


# ═══════════════════════════════════════════════════
# SECTION 3: CALCULATOR & MATH TOOLS
# ═══════════════════════════════════════════════════

def calculator(expression: str) -> str:
    """Safe calculator."""
    try:
        # Only allow safe math characters
        safe = expression.replace("^", "**").replace("×", "*").replace("÷", "/").replace(" ", "")
        if not re.match(r'^[\d+\-*/().%sqrt\s\*\^]+$', safe):
            return "❌ Invalid expression. Only numbers and basic operators allowed."
        # Remove 'sqrt' for safety - use math.sqrt instead
        safe_eval = re.sub(r'sqrt\(([^)]+)\)', r'math.sqrt(\1)', safe)
        result = eval(safe_eval, {"__builtins__": {}, "math": math})
        return f"🧮 *Result*\n\n`{expression}` = `{result}`"
    except ZeroDivisionError:
        return "❌ Cannot divide by zero!"
    except Exception as e:
        return f"❌ Calculation error: {str(e)[:80]}"


def bmi_calculator(weight_kg: float, height_cm: float) -> str:
    """Calculate BMI."""
    try:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"
        return f"⚖️ *BMI Result*\n\nBMI: *{bmi:.1f}*\nCategory: *{category}*\n\nWeight: {weight_kg} kg\nHeight: {height_cm} cm"
    except Exception as e:
        return f"❌ BMI calculation error: {str(e)[:80]}"


def tip_calculator(bill: float, tip_pct: float = 15, people: int = 1) -> str:
    """Calculate tip and split bill."""
    try:
        tip = bill * (tip_pct / 100)
        total = bill + tip
        per_person = total / people
        return (f"💰 *Tip Calculator*\n\n"
                f"Bill: ${bill:.2f}\n"
                f"Tip ({tip_pct}%): ${tip:.2f}\n"
                f"Total: ${total:.2f}\n"
                f"Per person ({people}): ${per_person:.2f}")
    except Exception as e:
        return f"❌ Tip calculation error: {str(e)[:80]}"


def percentage_calculator(part: float = None, whole: float = None, pct: float = None) -> str:
    """Calculate percentage."""
    try:
        if part is not None and whole is not None and whole != 0:
            result = (part / whole) * 100
            return f"📊 {part} is *{result:.2f}%* of {whole}"
        elif whole is not None and pct is not None:
            result = whole * (pct / 100)
            return f"📊 {pct}% of {whole} is *{result:.2f}*"
        else:
            return "❌ Provide part and whole (e.g., /percentage 25 200)"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def age_calculator(birth_date: str) -> str:
    """Calculate age from birth date. Format: YYYY-MM-DD"""
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        days_lived = (today - birth).days
        next_bday = birth.replace(year=today.year)
        if next_bday < today:
            next_bday = next_bday.replace(year=today.year + 1)
        days_until = (next_bday - today).days

        return (f"🎂 *Age Calculator*\n\n"
                f"Age: *{age} years old*\n"
                f"Days lived: *{days_lived:,}*\n"
                f"Next birthday in: *{days_until} days*")
    except ValueError:
        return "❌ Invalid date format. Use YYYY-MM-DD (e.g., 2000-01-15)"


def date_diff(date1: str, date2: str) -> str:
    """Days between two dates. Format: YYYY-MM-DD"""
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        diff = abs((d2 - d1).days)
        weeks = diff // 7
        days = diff % 7
        return f"📅 *Date Difference*\n\nDays between: *{diff} days*\nThat's {weeks} weeks and {days} days"
    except ValueError:
        return "❌ Invalid date format. Use YYYY-MM-DD for both dates."


# ═══════════════════════════════════════════════════
# SECTION 4: TEXT TOOLS
# ═══════════════════════════════════════════════════

def word_counter(text: str) -> str:
    """Count words in text."""
    words = len(text.split())
    return f"📊 *Word Count*\n\nWords: *{words}*"


def char_counter(text: str) -> str:
    """Count characters."""
    chars = len(text)
    no_spaces = len(text.replace(" ", ""))
    return f"📊 *Character Count*\n\nTotal: *{chars}*\nWithout spaces: *{no_spaces}*"


def text_case(text: str, mode: str) -> str:
    """Convert text case."""
    try:
        if mode == "upper":
            return f"🔠 *UPPERCASE*\n\n{text.upper()}"
        elif mode == "lower":
            return f"🔡 *lowercase*\n\n{text.lower()}"
        elif mode == "title":
            return f"📝 *Title Case*\n\n{text.title()}"
        elif mode == "sentence":
            return f"📝 *Sentence case*\n\n{text.capitalize()}"
        elif mode == "reverse":
            return f"🔄 *Reversed*\n\n{text[::-1]}"
        else:
            return "❌ Unknown mode. Use: upper, lower, title, sentence, reverse"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def reverse_text(text: str) -> str:
    return f"🔄 *Reversed*\n\n{text[::-1]}"


def text_statistics(text: str) -> str:
    """Detailed text statistics."""
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    char_no_spaces = len(text.replace(" ", ""))
    sentences = len(re.split(r'[.!?]+', text))
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    reading_time = max(1, math.ceil(word_count / 200))
    speaking_time = max(1, math.ceil(word_count / 130))

    return (f"📊 *Text Statistics*\n\n"
            f"Words: *{word_count}*\n"
            f"Characters: *{char_count}*\n"
            f"Characters (no spaces): *{char_no_spaces}*\n"
            f"Sentences: *{sentences}*\n"
            f"Avg word length: *{avg_word_len:.1f}*\n"
            f"Reading time: ~*{reading_time} min*\n"
            f"Speaking time: ~*{speaking_time} min*")


def define_word(word: str) -> str:
    """Define a word using free dictionary API."""
    try:
        resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
        if resp.status_code != 200:
            return f"❌ Could not find definition for '{word}'"
        data = resp.json()
        result = f"📖 *Definition of: {word}*\n\n"
        for entry in data[:2]:
            meanings = entry.get("meanings", [])
            for m in meanings[:2]:
                pos = m.get("partOfSpeech", "")
                defs = m.get("definitions", [])
                result += f"*({pos})*\n"
                for d in defs[:2]:
                    result += f"• {d.get('definition', '')}\n"
                result += "\n"
            phonetic = entry.get("phonetic", "")
            if phonetic:
                result += f"🔊 Pronunciation: {phonetic}\n"
        return result
    except Exception as e:
        return f"❌ Definition lookup failed: {str(e)[:80]}"


def synonym_finder(word: str) -> str:
    """Find synonyms."""
    try:
        resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
        if resp.status_code != 200:
            return f"❌ Could not find synonyms for '{word}'"
        data = resp.json()
        synonyms = []
        for entry in data:
            for m in entry.get("meanings", []):
                for d in m.get("definitions", []):
                    synonyms.extend(d.get("synonyms", [])[:3])
        synonyms = list(set(synonyms))[:8]
        if not synonyms:
            return f"❌ No synonyms found for '{word}'"
        return f"🔄 *Synonyms of: {word}*\n\n" + ", ".join(f"*{s}*" for s in synonyms)
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def antonym_finder(word: str) -> str:
    """Find antonyms."""
    try:
        resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
        if resp.status_code != 200:
            return f"❌ Could not find antonyms for '{word}'"
        data = resp.json()
        antonyms = []
        for entry in data:
            for m in entry.get("meanings", []):
                for d in m.get("definitions", []):
                    antonyms.extend(d.get("antonyms", [])[:3])
        antonyms = list(set(antonyms))[:8]
        if not antonyms:
            return f"❌ No antonyms found for '{word}'"
        return f"↩️ *Antonyms of: {word}*\n\n" + ", ".join(f"*{a}*" for a in antonyms)
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def morse_encode(text: str) -> str:
    """Encode text to morse code."""
    MORSE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
        '8': '---..', '9': '----.', ' ': '/'
    }
    result = []
    for char in text.upper():
        if char in MORSE:
            result.append(MORSE[char])
        else:
            result.append(char)
    return f"📡 *Morse Code*\n\n{' '.join(result)}"


def morse_decode(morse: str) -> str:
    """Decode morse code to text."""
    MORSE_REVERSE = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
        '---..': '8', '----.': '9', '/': ' '
    }
    try:
        result = []
        for code in morse.split():
            if code in MORSE_REVERSE:
                result.append(MORSE_REVERSE[code])
            else:
                result.append(code)
        return f"🔤 *Decoded Morse*\n\n{''.join(result)}"
    except Exception as e:
        return f"❌ Decode error: {str(e)[:80]}"


def text_to_binary(text: str) -> str:
    """Convert text to binary."""
    try:
        binary = ' '.join(format(ord(c), '08b') for c in text)
        return f"💾 *Binary*\n\n`{binary}`"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def binary_to_text(binary: str) -> str:
    """Convert binary to text."""
    try:
        text = ''.join(chr(int(b, 2)) for b in binary.split())
        return f"🔤 *From Binary*\n\n{text}"
    except Exception as e:
        return f"❌ Invalid binary input."


def text_repeat(text: str, count: int = 3) -> str:
    """Repeat text."""
    result = (text + " ") * count
    return f"🔁 *Repeated {count}x*\n\n{result.strip()}"


# ═══════════════════════════════════════════════════
# SECTION 5: ENCODING & CRYPTO TOOLS
# ═══════════════════════════════════════════════════

def base64_encode(text: str) -> str:
    """Encode text to base64."""
    try:
        encoded = base64.b64encode(text.encode()).decode()
        return f"🔐 *Base64 Encoded*\n\n`{encoded}`"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def base64_decode(text: str) -> str:
    """Decode base64 to text."""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return f"🔓 *Base64 Decoded*\n\n{decoded}"
    except Exception:
        return "❌ Invalid Base64 string."


def hash_generator(text: str) -> str:
    """Generate hashes of text."""
    try:
        md5 = hashlib.md5(text.encode()).hexdigest()
        sha1 = hashlib.sha1(text.encode()).hexdigest()
        sha256 = hashlib.sha256(text.encode()).hexdigest()
        return (f"🔐 *Hashes*\n\n"
                f"MD5: `{md5}`\n\n"
                f"SHA1: `{sha1}`\n\n"
                f"SHA256: `{sha256}`")
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def password_generator(length: int = 16) -> str:
    """Generate a strong password."""
    try:
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(length))
        strength = "🔴 Weak"
        if length >= 8:
            strength = "🟡 Medium"
        if length >= 12:
            strength = "🟢 Strong"
        if length >= 16:
            strength = "💚 Very Strong"
        return f"🔐 *Generated Password*\n\n`{password}`\n\nLength: {length} | Strength: {strength}\n\n⚠️ Save this somewhere safe!"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def password_strength(password: str) -> str:
    """Check password strength."""
    score = 0
    feedback = []
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    if len(password) >= 12:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Add uppercase letters")
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Add lowercase letters")
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Add numbers")
    if any(c in string.punctuation for c in password):
        score += 1
    else:
        feedback.append("Add special characters (!@#$%...)")

    if score <= 2:
        level = "🔴 Very Weak"
    elif score <= 3:
        level = "🟠 Weak"
    elif score <= 4:
        level = "🟡 Medium"
    elif score == 5:
        level = "🟢 Strong"
    else:
        level = "💚 Very Strong"

    tips = "\n".join(f"• {f}" for f in feedback)
    return f"🔒 *Password Strength*\n\nScore: {score}/6\nLevel: *{level}*\n\n💡 Tips:\n{tips if tips else '• Looks great!'}"


def email_validator(email: str) -> str:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        domain = email.split("@")[1]
        return f"✅ *Valid Email*\n\nEmail: {email}\nDomain: {domain}"
    return f"❌ *Invalid Email*\n\n'{email}' is not a valid email address."


# ═══════════════════════════════════════════════════
# SECTION 6: CONVERTERS
# ═══════════════════════════════════════════════════

def currency_convert(amount: float, from_curr: str, to_curr: str) -> str:
    """Convert currency using free API."""
    try:
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get(to_curr)
        if not rate:
            return f"❌ Currency '{to_curr}' not found."
        result = amount * rate
        return (f"💱 *Currency Conversion*\n\n"
                f"{amount:,.2f} {from_curr} = *{result:,.2f} {to_curr}*\n"
                f"Rate: 1 {from_curr} = {rate:.4f} {to_curr}")
    except Exception as e:
        return f"❌ Conversion failed: {str(e)[:80]}"


def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """Common unit conversions."""
    conversions = {
        ("km", "mi"): 0.621371, ("mi", "km"): 1.60934,
        ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
        ("cm", "in"): 0.393701, ("in", "cm"): 2.54,
        ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
        ("c", "f"): lambda v: v * 9/5 + 32, ("f", "c"): lambda v: (v - 32) * 5/9,
        ("l", "gal"): 0.264172, ("gal", "l"): 3.78541,
        ("m", "yd"): 1.09361, ("yd", "m"): 0.9144,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        factor = conversions[key]
        if callable(factor):
            result = factor(value)
        else:
            result = value * factor
        return f"📐 *Unit Conversion*\n\n{value} {from_unit} = *{result:.4f} {to_unit}*"
    return f"❌ Unknown conversion: {from_unit} → {to_unit}\n\nSupported: km↔mi, kg↔lb, cm↔in, m↔ft, C↔F, l↔gal, m↔yd"


def color_info(color: str) -> str:
    """Get color information from hex code."""
    try:
        color = color.lstrip("#")
        if len(color) != 6:
            return "❌ Use 6-digit hex code (e.g., FF5733 or #FF5733)"
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        # Brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "White" if brightness < 128 else "Black"
        # RGB to HSL approximation
        rf, gf, bf = r/255, g/255, b/255
        mx = max(rf, gf, bf)
        mn = min(rf, gf, bf)
        l = (mx + mn) / 2
        if mx == mn:
            h = s = 0
        else:
            d = mx - mn
            s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
            if mx == rf:
                h = (gf - bf) / d + (6 if gf < bf else 0)
            elif mx == gf:
                h = (bf - rf) / d + 2
            else:
                h = (rf - gf) / d + 4
            h /= 6
        return (f"🎨 *Color Info: #{color.upper()}*\n\n"
                f"RGB: ({r}, {g}, {b})\n"
                f"HSL: ({h*360:.0f}°, {s*100:.0f}%, {l*100:.0f}%)\n"
                f"Brightness: {brightness:.0f}/255\n"
                f"Best text color: *{text_color}*")
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def random_color() -> str:
    """Generate a random color."""
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    hex_color = f"#{r:02X}{g:02X}{b:02X}"
    return f"🎨 *Random Color*\n\n{hex_color}\nRGB: ({r}, {g}, {b})\n\n⬛ A sample would look like this color!"


def roman_to_int(roman: str) -> str:
    """Convert roman numeral to integer."""
    try:
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        prev = 0
        for char in reversed(roman):
            if char not in values:
                return f"❌ Invalid roman numeral: {char}"
            val = values[char]
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
        return f"🔢 *Roman to Integer*\n\n{roman} = *{total}*"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def int_to_roman(num: int) -> str:
    """Convert integer to roman numeral."""
    try:
        num = int(num)
        if not 1 <= num <= 3999:
            return "❌ Number must be between 1 and 3999"
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        sym = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        roman = ""
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman += sym[i]
                num -= val[i]
            i += 1
        return f"🔢 *Integer to Roman*\n\n{int(num) if num == 0 else ''} → *{roman}*"
    except ValueError:
        return "❌ Please provide a valid number."
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


# ═══════════════════════════════════════════════════
# SECTION 7: FUN & GAMES
# ═══════════════════════════════════════════════════

def coin_flip() -> str:
    result = random.choice([" heads 🪙", " tails 🪙"])
    return f"🪙 *Coin Flip*\n\nIt landed on*{result}*!"


def dice_roll(count: int = 1) -> str:
    results = [random.randint(1, 6) for _ in range(count)]
    total = sum(results)
    dice_str = " + ".join(str(r) for r in results)
    return f"🎲 *Dice Roll*\n\n{dice_str} = *{total}*"


def random_number(min_val: int = 1, max_val: int = 100) -> str:
    result = random.randint(min_val, max_val)
    return f"🎯 *Random Number*\n\nBetween {min_val} and {max_val}: *{result}*"


def rock_paper_scissors(choice: str) -> str:
    choice = choice.lower().strip()
    options = ["rock", "paper", "scissors"]
    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    if choice not in options:
        return f"❌ Choose: rock, paper, or scissors"
    bot_choice = random.choice(options)
    if choice == bot_choice:
        result = "🤝 *It's a draw!*"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "🎉 *You win!*"
    else:
        result = "😤 *I win!*"
    return (f"🪨📄✂️ *Rock Paper Scissors*\n\n"
            f"You: {emojis.get(choice, choice)} {choice}\n"
            f"Bot: {emojis.get(bot_choice, bot_choice)} {bot_choice}\n\n"
            f"{result}")


def roulette() -> str:
    """Russian roulette - just for fun!"""
    chamber = random.randint(1, 6)
    if chamber == 1:
        return "🔫 *BANG!* 💀\n\nYou're out! Better luck next time..."
    return f"🔫 *Click...* 😮‍💨\n\nYou survived! Chamber {chamber}/6 was empty."


def riddle() -> str:
    """Get a riddle."""
    riddles = [
        ("I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "A map"),
        ("What has keys but no locks?", "A piano"),
        ("What has hands but can't clap?", "A clock"),
        ("I speak without a mouth and hear without ears. What am I?", "An echo"),
        ("The more you take, the more you leave behind. What am I?", "Footsteps"),
        ("What gets wetter the more it dries?", "A towel"),
        ("I can be cracked, made, told, and played. What am I?", "A joke"),
        ("What has a head and a tail but no body?", "A coin"),
        ("What begins with T, ends with T, and has T in it?", "A teapot"),
        ("What can travel around the world while staying in a corner?", "A stamp"),
        ("I'm tall when I'm young and short when I'm old. What am I?", "A candle"),
        ("What month of the year has 28 days?", "All of them"),
    ]
    q, a = random.choice(riddles)
    return f"🤔 *Riddle*\n\n{q}\n\n||{a}|| *(tap to reveal answer)*"


def trivia() -> str:
    """Get a trivia question."""
    questions = [
        ("What is the largest planet in our solar system?", "Jupiter"),
        ("What year did the Titanic sink?", "1912"),
        ("What element does 'O' represent?", "Oxygen"),
        ("How many continents are there?", "7"),
        ("What is the speed of light (approx)?", "300,000 km/s"),
        ("Who painted the Mona Lisa?", "Leonardo da Vinci"),
        ("What is the smallest country in the world?", "Vatican City"),
        ("What is the hardest natural substance?", "Diamond"),
        ("How many bones in the human body?", "206"),
        ("What is the chemical formula for water?", "H₂O"),
        ("Who wrote Romeo and Juliet?", "Shakespeare"),
        ("What is the longest river in the world?", "Nile"),
    ]
    q, a = random.choice(questions)
    return f"🧠 *Trivia*\n\n{q}\n\n||{a}|| *(tap to reveal answer)*"


def truth_or_dare() -> str:
    """Get a truth or dare."""
    truths = [
        "What's the last lie you told?",
        "What's your most embarrassing moment?",
        "What's a secret you've never told anyone?",
        "What's the craziest thing you've done?",
        "What's your biggest fear?",
        "Who in this chat do you trust the most?",
        "What's the worst gift you've ever received?",
        "What's a weird habit you have?",
    ]
    dares = [
        "Send a voice note singing your favorite song.",
        "Do 10 pushups right now!",
        "Send your most used emoji 10 times.",
        "Let someone in this chat change your profile pic for 5 minutes.",
        "Say 'I'm a potato' out loud.",
        "Share the last photo in your camera roll.",
        "Type a paragraph using only your nose to type.",
        "Send a message to your best friend saying 'I'm an alien'.",
    ]
    if random.random() < 0.5:
        return f"🎭 *Truth*\n\n{random.choice(truths)}"
    return f"🎮 *Dare*\n\n{random.choice(dares)}"


def would_you_rather() -> str:
    """Would you rather question."""
    questions = [
        "Have the ability to fly 🦅 OR be invisible 👻",
        "Only eat pizza 🍕 OR only eat tacos 🌮 for the rest of your life",
        "Live in the past 🕰️ OR live in the future 🚀",
        "Have unlimited money 💰 OR unlimited time ⏰",
        "Be famous 🌟 OR be the best friend of someone famous",
        "Always be 10 minutes late ⏰ OR always be 20 minutes early",
        "Have a rewind button ⏪ OR a pause button ⏸️ for your life",
        "Speak every language 🗣️ OR be able to talk to animals 🐾",
        "Live without music 🎵 OR live without movies 🎬",
        "Have a personal chef 👨‍🍳 OR a personal trainer 💪",
    ]
    return f"🤔 *Would You Rather...*\n\n{random.choice(questions)}"


def get_joke() -> str:
    """Get a random joke."""
    try:
        resp = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return f"😂 *Joke*\n\n{data['setup']}\n\n{data['punchline']}"
    except Exception:
        pass
    # Fallback jokes
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "I'm reading a book about anti-gravity. It's impossible to put down!",
        "Why don't eggs tell jokes? They'd crack each other up!",
    ]
    return f"😂 *Joke*\n\n{random.choice(jokes)}"


def get_quote() -> str:
    """Get a motivational quote."""
    try:
        resp = requests.get("https://api.quotable.io/random", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return f"💬 *Quote*\n\n\"{data['content']}\"\n— {data['author']}"
    except Exception:
        pass
    # Fallback
    quotes = [
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
        ("Life is what happens when you're busy making other plans.", "John Lennon"),
        ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
        ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
    ]
    q, a = random.choice(quotes)
    return f"💬 *Quote*\n\n\"{q}\"\n— {a}"


def get_fact() -> str:
    """Get a random fact."""
    try:
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return f"🧠 *Did You Know?*\n\n{data['text']}"
    except Exception:
        pass
    facts = [
        "Honey never spoils. Archaeologists have found 3,000-year-old honey in Egyptian tombs that was still edible.",
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts and blue blood.",
        "Bananas are berries, but strawberries aren't.",
        "The shortest war in history lasted 38 minutes (between Britain and Zanzibar).",
    ]
    return f"🧠 *Did You Know?*\n\n{random.choice(facts)}"


def get_compliment() -> str:
    """Get a random compliment."""
    compliments = [
        "You're an amazing person! Never forget that! ✨",
        "The world is a better place with you in it! 🌟",
        "You have an incredible energy that inspires everyone around you! 💫",
        "Your kindness makes a real difference! 🌈",
        "You're smarter than you think and stronger than you know! 💪",
        "Someone out there is smiling because of you! 😊",
        "You have a gift for making people feel special! 🎁",
        "Your potential is limitless! Keep going! 🚀",
    ]
    return f"💛 *Compliment*\n\n{random.choice(compliments)}"


def get_advice() -> str:
    """Get random advice."""
    advices = [
        "Don't compare yourself to others. Your journey is unique. 🛤️",
        "Take a deep breath. Everything will be okay. 🌊",
        "Start before you're ready. You'll figure it out along the way. 🏃",
        "It's okay to say no. Your peace matters more than their approval. 🙅",
        "Sleep is not a luxury, it's a necessity. Take care of yourself. 😴",
        "Progress, not perfection. Small steps lead to big changes. 🐢",
        "Surround yourself with people who lift you up. 🎈",
        "The best time to start was yesterday. The next best time is now. ⏰",
    ]
    return f"🎯 *Advice*\n\n{random.choice(advices)}"


def get_pickup_line() -> str:
    """Get a pickup line (fun)."""
    lines = [
        "Are you a magician? Because whenever I look at you, everyone else disappears! ✨",
        "Do you have a map? I keep getting lost in your eyes! 🗺️",
        "Are you a campfire? Because you're hot and I want s'more! 🔥",
        "If you were a vegetable, you'd be a cute-cumber! 🥒",
        "Do you believe in love at first sight, or should I walk by again? 👀",
        "Are you a Wi-Fi signal? Because I'm feeling a connection! 📶",
        "Is your name Google? Because you have everything I've been searching for! 🔍",
    ]
    return f"😘 *Pickup Line*\n\n{random.choice(lines)}"


def get_motivation() -> str:
    """Get motivational message."""
    messages = [
        "🔥 You didn't come this far to only come this far. Keep pushing!",
        "💪 Every expert was once a beginner. Don't give up!",
        "⭐ Your only limit is you. Break free from your doubts!",
        "🚀 The pain you feel today will be the strength you feel tomorrow.",
        "🌟 Great things never come from comfort zones. Take that leap!",
        "🎯 Focus on the step in front of you, not the whole staircase.",
        "🔥 You are capable of amazing things. Believe in yourself!",
        "💎 Hard work beats talent when talent doesn't work hard.",
    ]
    return f"🔥 *Daily Motivation*\n\n{random.choice(messages)}"


def emojify(text: str) -> str:
    """Add emojis to text (fun)."""
    try:
        prompt = f"Rewrite this text by adding relevant emojis throughout it. Keep the original meaning. Only output the emojified version:\n\n{text}"
        result = chat_single(prompt, "You add fun, relevant emojis to text. Output only the emojified text.")
        return f"😊 *Emojified*\n\n{result}"
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def lorem_ipsum(count: int = 3) -> str:
    """Generate lorem ipsum paragraphs."""
    base = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
            "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
            "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure "
            "dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
            "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
            "mollit anim id est laborum.")
    paragraphs = "\n\n".join(base for _ in range(count))
    return f"📝 *Lorem Ipsum* ({count} paragraphs)\n\n{paragraphs}"


# ═══════════════════════════════════════════════════
# SECTION 8: UTILITY & INFO TOOLS
# ═══════════════════════════════════════════════════

def timezone_info(tz_name: str = "UTC") -> str:
    """Get timezone info."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        utc_now = datetime.utcnow()
        offset = now.strftime("%z")
        return (f"🌍 *Timezone Info: {tz_name}*\n\n"
                f"Current time: *{now.strftime('%Y-%m-%d %H:%M:%S %Z')}*\n"
                f"UTC offset: {offset}\n"
                f"UTC time: {utc_now.strftime('%H:%M:%S')}")
    except Exception:
        return f"❌ Unknown timezone: {tz_name}\n\nTry: UTC, America/New_York, Europe/London, Asia/Tokyo, Asia/Kolkata"


def country_info(country: str) -> str:
    """Get country information."""
    try:
        resp = requests.get(f"https://restcountries.com/v3.1/name/{country}", timeout=10)
        if resp.status_code != 200:
            return f"❌ Country '{country}' not found."
        data = resp.json()[0]
        name = data.get("name", {}).get("common", country)
        capital = data.get("capital", ["N/A"])[0]
        region = data.get("region", "N/A")
        population = data.get("population", 0)
        area = data.get("area", 0)
        currencies = data.get("currencies", {})
        curr_str = ", ".join(f"{v.get('name', '')} ({k})" for k, v in currencies.items())
        languages = data.get("languages", {})
        lang_str = ", ".join(languages.values())
        flag = data.get("flag", "")

        return (f"🗺️ *Country: {flag} {name}*\n\n"
                f"Capital: *{capital}*\n"
                f"Region: {region}\n"
                f"Population: *{population:,}*\n"
                f"Area: *{area:,} km²*\n"
                f"Currencies: {curr_str}\n"
                f"Languages: {lang_str}")
    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


def periodic_table(element: str) -> str:
    """Get periodic table element info."""
    try:
        resp = requests.get(f"https://periodictable.p.rapidapi.com/element/{element}",
                           headers={"X-RapidAPI-Key": "none"}, timeout=5)
    except Exception:
        pass
    # Use built-in data instead
    elements = {
        "H": ("Hydrogen", 1, 1.008, "Nonmetal"),
        "He": ("Helium", 2, 4.003, "Noble Gas"),
        "C": ("Carbon", 6, 12.011, "Nonmetal"),
        "N": ("Nitrogen", 7, 14.007, "Nonmetal"),
        "O": ("Oxygen", 8, 15.999, "Nonmetal"),
        "Fe": ("Iron", 26, 55.845, "Transition Metal"),
        "Au": ("Gold", 79, 196.967, "Transition Metal"),
        "Ag": ("Silver", 47, 107.868, "Transition Metal"),
        "Cu": ("Copper", 29, 63.546, "Transition Metal"),
        "Na": ("Sodium", 11, 22.990, "Alkali Metal"),
        "K": ("Potassium", 19, 39.098, "Alkali Metal"),
        "Ca": ("Calcium", 20, 40.078, "Alkaline Earth"),
        "Zn": ("Zinc", 30, 65.38, "Transition Metal"),
        "Pb": ("Lead", 82, 207.2, "Transition Metal"),
        "U": ("Uranium", 92, 238.029, "Actinide"),
        "Ne": ("Neon", 10, 20.180, "Noble Gas"),
        "Cl": ("Chlorine", 17, 35.45, "Halogen"),
        "S": ("Sulfur", 16, 32.06, "Nonmetal"),
        "P": ("Phosphorus", 15, 30.974, "Nonmetal"),
        "Al": ("Aluminum", 13, 26.982, "Post-transition Metal"),
    }
    symbol = element.upper()
    if symbol in elements:
        name, number, mass, category = elements[symbol]
        return (f"⚛️ *Element: {symbol}*\n\n"
                f"Name: *{name}*\n"
                f"Atomic Number: *{number}*\n"
                f"Atomic Mass: *{mass}*\n"
                f"Category: {category}")
    return f"❌ Element '{element}' not found. Try: H, He, C, N, O, Fe, Au, Ag, Cu, Na, etc."


def ip_lookup(ip: str = "") -> str:
    """Look up IP address info."""
    try:
        url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return "❌ Could not look up IP address."
        data = resp.json()
        return (f"🌐 *IP Information*\n\n"
                f"IP: *{data.get('ip', 'N/A')}*\n"
                f"City: {data.get('city', 'N/A')}\n"
                f"Region: {data.get('region', 'N/A')}\n"
                f"Country: {data.get('country_name', 'N/A')} ({data.get('country_code', '')})\n"
                f"ISP: {data.get('org', 'N/A')}\n"
                f"Timezone: {data.get('timezone', 'N/A')}")
    except Exception as e:
        return f"❌ Lookup failed: {str(e)[:80]}"
