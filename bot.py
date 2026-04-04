"""
bot.py — AgentX Telegram Bot (v2.0 — Complete Rewrite)
ALL features, NO API keys needed (Pollinations.ai is free).
Deployed on Render.com with Flask health server.

Architecture:
  - Main thread: Flask HTTP server (health check for Render)
  - Background thread: Telegram bot (asyncio event loop)
  - Every handler gets user_id FIRST, then processes.
  - Every handler has its own try/except.
  - Error handler is extra safe with fallback user_id.
"""

import os
import sys
import json
import logging
import asyncio
import threading
import re
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8697860970:AAG-4ZKF5y-Rsmm7pxNUPv5pbLURtwe5uYI")
PORT = int(os.environ.get("PORT", 5000))

# ═══════════════════════════════════════════════════
# IMPORT BOT LIBRARIES
# ═══════════════════════════════════════════════════

from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# Our modules
import db
from ai import chat, generate_image
import tools

# ═══════════════════════════════════════════════════
# FLASK HEALTH SERVER
# ═══════════════════════════════════════════════════

flask_app = Flask(__name__)


@flask_app.route("/")
def health_check():
    """Render health check endpoint."""
    return jsonify({"status": "ok", "bot": "AgentX", "time": datetime.now(timezone.utc).isoformat()})


@flask_app.route("/health")
def health():
    return jsonify({"status": "healthy"})


# ═══════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════

def safe_get_user_id(update: Update) -> int:
    """Safely extract user_id from update. Returns 0 if unavailable."""
    try:
        if update.effective_user and update.effective_user.id:
            return update.effective_user.id
    except Exception:
        pass
    try:
        if update.message and update.message.from_user:
            return update.message.from_user.id
    except Exception:
        pass
    try:
        if update.callback_query and update.callback_query.from_user:
            return update.callback_query.from_user.id
    except Exception:
        pass
    return 0


def register_user(update: Update):
    """Register/update user in database."""
    try:
        user = update.effective_user
        if user:
            db.register_user(
                user.id,
                user.username or "",
                user.first_name or ""
            )
    except Exception as e:
        logger.error(f"Register user error: {e}")


def split_long_message(text: str, max_len: int = 4096) -> list:
    """Split long text into Telegram-compatible chunks."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Find a good break point
        break_idx = text.rfind("\n", 0, max_len)
        if break_idx == -1:
            break_idx = text.rfind(" ", 0, max_len)
        if break_idx == -1:
            break_idx = max_len
        chunks.append(text[:break_idx])
        text = text[break_idx:].lstrip()
    return chunks


async def safe_reply(update: Update, text: str, parse_mode: str = "Markdown"):
    """Safely reply to a message, handling long text and parse errors."""
    try:
        chunks = split_long_message(text)
        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode=parse_mode)
            except Exception:
                # If markdown fails, try without
                try:
                    await update.message.reply_text(chunk)
                except Exception as e:
                    logger.error(f"Reply failed: {e}")
    except Exception as e:
        logger.error(f"Safe reply error: {e}")


# ═══════════════════════════════════════════════════
# COMMAND HANDLERS
# Every handler: get user_id FIRST, then process.
# Every handler: own try/except.
# ═══════════════════════════════════════════════════

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command — welcome message."""
    user_id = safe_get_user_id(update)
    try:
        register_user(update)
        text = (
            "👋 *Welcome to AgentX!* 🤖\n\n"
            "I'm your personal AI assistant — free, fast, and feature-packed!\n\n"
            "🧠 *Chat with me* — just type anything\n"
            "🔍 /search — Web search\n"
            "📰 /news — Latest news\n"
            "🖼️ /image — Generate AI image\n"
            "💻 /code — Generate code\n"
            "🔧 /debug — Debug code\n"
            "📖 /explain — Explain code\n"
            "📚 /flashcards — Create flashcards\n"
            "📝 /quiz — Take a quiz\n"
            "🌐 /translate — Translate text\n"
            "🧮 /calc — Calculator\n"
            "📖 /define — Define a word\n"
            "🔐 /password — Generate password\n"
            "🔗 /summarize_url — Summarize a website\n"
            "📋 /summarize — Summarize text\n"
            "✍️ /rewrite — Rewrite text\n"
            "⚖️ /compare — Compare two things\n"
            "📖 /story — Generate a story\n"
            "🎵 /poem — Generate a poem\n"
            "🔢 /math — Solve math problems\n"
            "🔤 /morse — Morse code\n"
            "💾 /binary — Binary converter\n"
            "🔐 /hash — Generate hashes\n"
            "🔐 /base64 — Base64 encode/decode\n"
            "💱 /currency — Currency converter\n"
            "📐 /unit — Unit converter\n"
            "🎨 /color — Color info\n"
            "📐 /bmi — BMI calculator\n"
            "💰 /tip — Tip calculator\n"
            "📊 /percentage — Percentage calculator\n"
            "🎂 /age — Age calculator\n"
            "📅 /datediff — Days between dates\n"
            "📊 /stats — Text statistics\n"
            "🔤 /case — Change text case\n"
            "🔄 /reverse — Reverse text\n"
            "🔄 /synonym — Find synonyms\n"
            "↩️ /antonym — Find antonyms\n"
            "🔢 /roman — Roman numeral converter\n"
            "🔒 /pstrength — Password strength\n"
            "✉️ /emailcheck — Validate email\n"
            "🌍 /timezone — Timezone info\n"
            "🗺️ /country — Country info\n"
            "⚛️ /element — Periodic table\n"
            "🌐 /iplookup — IP address info\n"
            "🪙 /coinflip — Flip a coin\n"
            "🎲 /dice — Roll a dice\n"
            "🎯 /random — Random number\n"
            "🪨 /rps — Rock paper scissors\n"
            "🔫 /roulette — Russian roulette\n"
            "🤔 /riddle — Get a riddle\n"
            "🧠 /trivia — Trivia question\n"
            "🎭 /tod — Truth or dare\n"
            "🤔 /wyr — Would you rather\n"
            "😂 /joke — Random joke\n"
            "💬 /quote — Inspirational quote\n"
            "🧠 /fact — Random fact\n"
            "💛 /compliment — Get a compliment\n"
            "🎯 /advice — Get advice\n"
            "😘 /pickupline — Pickup line\n"
            "🔥 /motivation — Daily motivation\n"
            "😊 /emojify — Add emojis to text\n"
            "📝 /lorem — Lorem ipsum generator\n"
            "🎨 /randomcolor — Random color\n"
            "🔁 /repeat — Repeat text\n"
            "📝 /todo — Manage todos\n"
            "📒 /note — Manage notes\n"
            "🧠 /remember — Save a memory\n"
            "🧠 /memories — View memories\n"
            "🧹 /clear — Clear chat history\n"
            "❓ /help — Show this help\n\n"
            "_Type any of these commands or just chat with me!_"
        )
        await safe_reply(update, text)
    except Exception as e:
        logger.error(f"Start error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("👋 Welcome to AgentX! Type /help to see all features.")
        except Exception:
            pass


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command."""
    user_id = safe_get_user_id(update)
    try:
        await start_cmd(update, context)
    except Exception as e:
        logger.error(f"Help error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("Type /start to see all features!")
        except Exception:
            pass


# ── AI Chat (handles regular text messages) ──

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages — chat with AI."""
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        register_user(update)
        user_text = update.message.text.strip()

        if not user_text:
            return

        # Save user message to history
        db.save_message(user_id, "user", user_text)
        db.update_user_activity(user_id)

        # Get history for context
        history = db.get_history(user_id, limit=20)
        ai_messages = [{"role": h["role"], "content": h["content"]} for h in history]

        # Get AI response
        reply_text = chat(ai_messages)

        # Save AI response
        db.save_message(user_id, "assistant", reply_text)

        await safe_reply(update, reply_text)

    except Exception as e:
        logger.error(f"Message handler error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Something went wrong. Please try again!")
        except Exception:
            pass


# ═══════════════════════════════════════════════════
# FEATURE COMMANDS
# ═══════════════════════════════════════════════════

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        query = " ".join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text("🔍 Usage: /search <query>\n\nExample: /search Python tutorial")
            return
        result = tools.web_search(query)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Search error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Search failed. Try again!")
        except Exception:
            pass


async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        query = " ".join(context.args) if context.args else "technology"
        result = tools.search_news(query)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"News error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ News search failed.")
        except Exception:
            pass


async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        prompt = " ".join(context.args) if context.args else ""
        if not prompt:
            await update.message.reply_text("🖼️ Usage: /image <description>\n\nExample: /image A sunset over mountains")
            return
        # Send "generating" message first
        wait_msg = await update.message.reply_text("🖼️ Generating image... ⏳")
        # Generate the image URL
        image_url = generate_image(prompt)
        if not image_url:
            await wait_msg.edit_text("❌ Image generation failed.")
            return
        # Send the actual image as a photo
        try:
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🖼️ *{prompt}*",
                parse_mode="Markdown"
            )
            # Delete the waiting message
            try:
                await wait_msg.delete()
            except Exception:
                pass
        except Exception as photo_err:
            logger.error(f"Photo send failed (uid={user_id}): {photo_err}")
            # Fallback: send URL as text
            await wait_msg.edit_text(
                f"🖼️ *Generated Image*\n\n{image_url}\n\n⚠️ Could not send as image. Open the link above to view.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Image error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Image generation failed.")
        except Exception:
            pass


async def code_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        desc = " ".join(context.args) if context.args else ""
        if not desc:
            await update.message.reply_text("💻 Usage: /code <description>\n\nExample: /code A Python web scraper")
            return
        await update.message.reply_text("⏳ Generating code...")
        result = tools.gen_code(desc)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Code error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Code generation failed.")
        except Exception:
            pass


async def debug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        code = " ".join(context.args) if context.args else ""
        if not code:
            await update.message.reply_text("🔧 Usage: /debug <code>\n\nExample: /debug print('hello")
            return
        await update.message.reply_text("⏳ Analyzing code...")
        result = tools.debug_code(code)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Debug error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Debug failed.")
        except Exception:
            pass


async def explain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        code = " ".join(context.args) if context.args else ""
        if not code:
            await update.message.reply_text("📖 Usage: /explain <code>")
            return
        await update.message.reply_text("⏳ Explaining...")
        result = tools.explain_code(code)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Explain error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Explanation failed.")
        except Exception:
            pass


async def flashcards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        topic = " ".join(context.args) if context.args else ""
        if not topic:
            await update.message.reply_text("📚 Usage: /flashcards <topic>\n\nExample: /flashcards Photosynthesis")
            return
        await update.message.reply_text("⏳ Creating flashcards...")
        result = tools.gen_flashcards(topic)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Flashcards error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Flashcard generation failed.")
        except Exception:
            pass


async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        topic = " ".join(context.args) if context.args else ""
        if not topic:
            await update.message.reply_text("📝 Usage: /quiz <topic>\n\nExample: /quiz World War 2")
            return
        await update.message.reply_text("⏳ Creating quiz...")
        result = tools.gen_quiz(topic)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Quiz error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Quiz generation failed.")
        except Exception:
            pass


async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if not args:
            await update.message.reply_text("🌐 Usage: /translate <language> <text>\n\nExample: /translate Spanish Hello world")
            return
        lang = args[0]
        text = " ".join(args[1:])
        if not text:
            await update.message.reply_text("❌ Provide text to translate.")
            return
        await update.message.reply_text("⏳ Translating...")
        result = tools.translate_text(text, lang)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Translate error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Translation failed.")
        except Exception:
            pass


async def calc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        expr = " ".join(context.args) if context.args else ""
        if not expr:
            await update.message.reply_text("🧮 Usage: /calc <expression>\n\nExample: /calc (25 + 75) * 2")
            return
        result = tools.calculator(expr)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Calc error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Calculation failed.")
        except Exception:
            pass


async def define_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        word = " ".join(context.args) if context.args else ""
        if not word:
            await update.message.reply_text("📖 Usage: /define <word>\n\nExample: /define serendipity")
            return
        result = tools.define_word(word)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Define error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Definition lookup failed.")
        except Exception:
            pass


async def password_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        length = 16
        if context.args:
            try:
                length = int(context.args[0])
                if length < 4:
                    length = 4
                if length > 64:
                    length = 64
            except ValueError:
                pass
        result = tools.password_generator(length)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Password error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Password generation failed.")
        except Exception:
            pass


async def summarize_url_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        url = " ".join(context.args) if context.args else ""
        if not url:
            await update.message.reply_text("🔗 Usage: /summarize_url <URL>\n\nExample: /summarize_url https://example.com")
            return
        await update.message.reply_text("⏳ Summarizing URL...")
        result = tools.summarize_url(url)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Summarize URL error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ URL summarization failed.")
        except Exception:
            pass


async def summarize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("📋 Usage: /summarize <text>")
            return
        result = tools.summarize_text(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Summarize error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Summarization failed.")
        except Exception:
            pass


async def rewrite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if not args:
            await update.message.reply_text("✍️ Usage: /rewrite <style> <text>\n\nExample: /rewrite formal Hello guys")
            return
        style = args[0]
        text = " ".join(args[1:])
        if not text:
            text = style
            style = "better"
        result = tools.rewrite_text(text, style)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Rewrite error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Rewrite failed.")
        except Exception:
            pass


async def compare_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("⚖️ Usage: /compare <item1> <item2>\n\nExample: /compare Python JavaScript")
            return
        # Split by " vs " if present
        full = " ".join(args)
        if " vs " in full.lower():
            parts = re.split(r'\s+vs\s+', full, maxsplit=1, flags=re.IGNORECASE)
            item1, item2 = parts[0].strip(), parts[1].strip()
        else:
            item1, item2 = args[0], " ".join(args[1:])
        await update.message.reply_text("⏳ Comparing...")
        result = tools.compare_things(item1, item2)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Compare error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Comparison failed.")
        except Exception:
            pass


async def story_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        topic = " ".join(context.args) if context.args else "adventure"
        await update.message.reply_text("⏳ Writing story...")
        result = tools.gen_story(topic)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Story error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Story generation failed.")
        except Exception:
            pass


async def poem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        topic = " ".join(context.args) if context.args else "nature"
        await update.message.reply_text("⏳ Writing poem...")
        result = tools.gen_poem(topic)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Poem error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Poem generation failed.")
        except Exception:
            pass


async def math_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        problem = " ".join(context.args) if context.args else ""
        if not problem:
            await update.message.reply_text("🔢 Usage: /math <problem>\n\nExample: /math What is 15% of 240?")
            return
        await update.message.reply_text("⏳ Solving...")
        result = tools.solve_math(problem)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Math error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Math solving failed.")
        except Exception:
            pass


async def morse_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("📡 Usage: /morse <text>\n\nEncode text to morse code.")
            return
        # Detect if it's morse code (dots and dashes)
        if re.match(r'^[\.\-\/\s]+$', text):
            result = tools.morse_decode(text)
        else:
            result = tools.morse_encode(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Morse error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Morse conversion failed.")
        except Exception:
            pass


async def binary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("💾 Usage: /binary <text or binary>")
            return
        # Detect if binary
        if re.match(r'^[01\s]+$', text):
            result = tools.binary_to_text(text)
        else:
            result = tools.text_to_binary(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Binary error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Binary conversion failed.")
        except Exception:
            pass


async def hash_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("🔐 Usage: /hash <text>")
            return
        result = tools.hash_generator(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Hash error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Hash generation failed.")
        except Exception:
            pass


async def base64_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("🔐 Usage: /base64 <text to encode>")
            return
        # Try decode first if it looks like base64
        if re.match(r'^[A-Za-z0-9+/=]+$', text) and len(text) > 10:
            result = tools.base64_decode(text)
        else:
            result = tools.base64_encode(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Base64 error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Base64 operation failed.")
        except Exception:
            pass


async def currency_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 3:
            await update.message.reply_text("💱 Usage: /currency <amount> <from> <to>\n\nExample: /currency 100 USD EUR")
            return
        amount = float(args[0])
        from_c = args[1].upper()
        to_c = args[2].upper()
        result = tools.currency_convert(amount, from_c, to_c)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /currency <amount> <from> <to>\n\nExample: /currency 100 USD EUR")
    except Exception as e:
        logger.error(f"Currency error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Currency conversion failed.")
        except Exception:
            pass


async def unit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 3:
            await update.message.reply_text(
                "📐 Usage: /unit <value> <from> <to>\n\n"
                "Example: /unit 100 km mi\n\n"
                "Supported: km↔mi, kg↔lb, cm↔in, m↔ft, C↔F, l↔gal, m↔yd"
            )
            return
        value = float(args[0])
        from_u = args[1]
        to_u = args[2]
        result = tools.unit_convert(value, from_u, to_u)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /unit <value> <from> <to>")
    except Exception as e:
        logger.error(f"Unit error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Unit conversion failed.")
        except Exception:
            pass


async def color_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        color = " ".join(context.args) if context.args else ""
        if not color:
            await update.message.reply_text("🎨 Usage: /color <hex code>\n\nExample: /color FF5733")
            return
        result = tools.color_info(color)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Color error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Color lookup failed.")
        except Exception:
            pass


async def randomcolor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.random_color()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Random color error (uid={user_id}): {e}")


async def bmi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("📐 Usage: /bmi <weight_kg> <height_cm>\n\nExample: /bmi 70 175")
            return
        weight = float(args[0])
        height = float(args[1])
        result = tools.bmi_calculator(weight, height)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /bmi <weight_kg> <height_cm>")
    except Exception as e:
        logger.error(f"BMI error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ BMI calculation failed.")
        except Exception:
            pass


async def tip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 1:
            await update.message.reply_text("💰 Usage: /tip <bill> [tip_pct] [people]\n\nExample: /tip 50 15 2")
            return
        bill = float(args[0])
        tip_pct = float(args[1]) if len(args) > 1 else 15
        people = int(args[2]) if len(args) > 2 else 1
        result = tools.tip_calculator(bill, tip_pct, people)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /tip <bill> [tip_pct] [people]")
    except Exception as e:
        logger.error(f"Tip error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Tip calculation failed.")
        except Exception:
            pass


async def percentage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("📊 Usage: /percentage <part> <whole>\n\nExample: /percentage 25 200")
            return
        part = float(args[0])
        whole = float(args[1])
        result = tools.percentage_calculator(part=part, whole=whole)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /percentage <part> <whole>")
    except Exception as e:
        logger.error(f"Percentage error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Calculation failed.")
        except Exception:
            pass


async def age_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        date_str = " ".join(context.args) if context.args else ""
        if not date_str:
            await update.message.reply_text("🎂 Usage: /age <YYYY-MM-DD>\n\nExample: /age 2000-06-15")
            return
        result = tools.age_calculator(date_str)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Age error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Age calculation failed.")
        except Exception:
            pass


async def datediff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("📅 Usage: /datediff <date1> <date2>\n\nExample: /datediff 2024-01-01 2024-12-31")
            return
        result = tools.date_diff(args[0], args[1])
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Datediff error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Date calculation failed.")
        except Exception:
            pass


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        # Use replied message or args
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
        else:
            text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("📊 Usage: /stats <text> or reply to a message with /stats")
            return
        result = tools.text_statistics(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Stats error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Stats failed.")
        except Exception:
            pass


async def case_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("🔤 Usage: /case <mode> <text>\n\nModes: upper, lower, title, sentence, reverse\n\nExample: /case upper hello world")
            return
        mode = args[0].lower()
        text = " ".join(args[1:])
        result = tools.text_case(text, mode)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Case error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Case conversion failed.")
        except Exception:
            pass


async def reverse_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("🔄 Usage: /reverse <text>")
            return
        result = tools.reverse_text(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Reverse error (uid={user_id}): {e}")


async def synonym_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        word = " ".join(context.args) if context.args else ""
        if not word:
            await update.message.reply_text("🔄 Usage: /synonym <word>")
            return
        result = tools.synonym_finder(word)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Synonym error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Synonym lookup failed.")
        except Exception:
            pass


async def antonym_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        word = " ".join(context.args) if context.args else ""
        if not word:
            await update.message.reply_text("↩️ Usage: /antonym <word>")
            return
        result = tools.antonym_finder(word)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Antonym error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Antonym lookup failed.")
        except Exception:
            pass


async def roman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("🔢 Usage: /roman <number or roman numeral>\n\nExample: /roman XLII or /roman 42")
            return
        # Detect if it's a number or roman
        if text.isdigit():
            result = tools.int_to_roman(int(text))
        else:
            result = tools.roman_to_int(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Roman error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Roman conversion failed.")
        except Exception:
            pass


async def pstrength_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        password = " ".join(context.args) if context.args else ""
        if not password:
            await update.message.reply_text("🔒 Usage: /pstrength <password>")
            return
        result = tools.password_strength(password)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Pstrength error (uid={user_id}): {e}")


async def emailcheck_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        email = " ".join(context.args) if context.args else ""
        if not email:
            await update.message.reply_text("✉️ Usage: /emailcheck <email>")
            return
        result = tools.email_validator(email)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Email check error (uid={user_id}): {e}")


async def timezone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        tz = " ".join(context.args) if context.args else "UTC"
        result = tools.timezone_info(tz)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Timezone error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Timezone lookup failed.")
        except Exception:
            pass


async def country_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        name = " ".join(context.args) if context.args else ""
        if not name:
            await update.message.reply_text("🗺️ Usage: /country <name>\n\nExample: /country Japan")
            return
        result = tools.country_info(name)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Country error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Country lookup failed.")
        except Exception:
            pass


async def element_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        elem = " ".join(context.args) if context.args else ""
        if not elem:
            await update.message.reply_text("⚛️ Usage: /element <symbol>\n\nExample: /element Au")
            return
        result = tools.periodic_table(elem)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Element error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Element lookup failed.")
        except Exception:
            pass


async def iplookup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        ip = " ".join(context.args) if context.args else ""
        result = tools.ip_lookup(ip)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"IP lookup error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ IP lookup failed.")
        except Exception:
            pass


# ── Fun & Games ──

async def coinflip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.coin_flip()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Coinflip error (uid={user_id}): {e}")


async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        count = 1
        if context.args:
            try:
                count = min(int(context.args[0]), 10)
            except ValueError:
                pass
        result = tools.dice_roll(count)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Dice error (uid={user_id}): {e}")


async def random_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        min_v, max_v = 1, 100
        if context.args and len(context.args) >= 2:
            try:
                min_v = int(context.args[0])
                max_v = int(context.args[1])
            except ValueError:
                pass
        result = tools.random_number(min_v, max_v)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Random error (uid={user_id}): {e}")


async def rps_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        choice = " ".join(context.args) if context.args else ""
        if not choice:
            await update.message.reply_text("🪨📄✂️ Usage: /rps <rock|paper|scissors>")
            return
        result = tools.rock_paper_scissors(choice)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"RPS error (uid={user_id}): {e}")


async def roulette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.roulette()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Roulette error (uid={user_id}): {e}")


async def riddle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.riddle()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Riddle error (uid={user_id}): {e}")


async def trivia_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.trivia()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Trivia error (uid={user_id}): {e}")


async def tod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.truth_or_dare()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"TOD error (uid={user_id}): {e}")


async def wyr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.would_you_rather()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"WYR error (uid={user_id}): {e}")


async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_joke()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Joke error (uid={user_id}): {e}")


async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_quote()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Quote error (uid={user_id}): {e}")


async def fact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_fact()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Fact error (uid={user_id}): {e}")


async def compliment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_compliment()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Compliment error (uid={user_id}): {e}")


async def advice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_advice()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Advice error (uid={user_id}): {e}")


async def pickupline_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_pickup_line()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Pickup line error (uid={user_id}): {e}")


async def motivation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        result = tools.get_motivation()
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Motivation error (uid={user_id}): {e}")


async def emojify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("😊 Usage: /emojify <text>")
            return
        await update.message.reply_text("⏳ Emojifying...")
        result = tools.emojify(text)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Emojify error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Emojify failed.")
        except Exception:
            pass


async def lorem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        count = 3
        if context.args:
            try:
                count = min(int(context.args[0]), 10)
            except ValueError:
                pass
        result = tools.lorem_ipsum(count)
        await safe_reply(update, result)
    except Exception as e:
        logger.error(f"Lorem error (uid={user_id}): {e}")


async def repeat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        args = context.args if context.args else []
        if len(args) < 2:
            await update.message.reply_text("🔁 Usage: /repeat <count> <text>\n\nExample: /repeat 5 Hello")
            return
        count = int(args[0])
        text = " ".join(args[1:])
        result = tools.text_repeat(text, count)
        await safe_reply(update, result)
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Usage: /repeat <count> <text>")
    except Exception as e:
        logger.error(f"Repeat error (uid={user_id}): {e}")


# ── Todo List ──

async def todo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        args = context.args if context.args else []
        if not args:
            # Show todos
            todos = db.get_todos(user_id)
            if not todos:
                await update.message.reply_text("📝 *Your Todo List* — empty!\n\nUse /todo add <task> to add items.")
                return
            text = "📝 *Your Todo List*\n\n"
            for t in todos:
                status = "✅" if t["done"] else "⬜"
                text += f"{status} [{t['id']}] {t['task']}\n"
            text += "\n/todo done <id> — Mark done\n/todo del <id> — Delete\n/todo add <task> — Add new"
            await safe_reply(update, text)
            return

        action = args[0].lower()

        if action == "add":
            task = " ".join(args[1:])
            if not task:
                await update.message.reply_text("❌ Provide a task: /todo add <task>")
                return
            tid = db.add_todo(user_id, task)
            await update.message.reply_text(f"✅ Todo added! (ID: {tid})\n\n{task}")

        elif action == "done":
            if len(args) < 2:
                await update.message.reply_text("❌ Provide ID: /todo done <id>")
                return
            tid = int(args[1])
            if db.toggle_todo(user_id, tid):
                await update.message.reply_text(f"✅ Toggled todo #{tid}")
            else:
                await update.message.reply_text(f"❌ Todo #{tid} not found.")

        elif action == "del":
            if len(args) < 2:
                await update.message.reply_text("❌ Provide ID: /todo del <id>")
                return
            tid = int(args[1])
            if db.delete_todo(user_id, tid):
                await update.message.reply_text(f"🗑️ Deleted todo #{tid}")
            else:
                await update.message.reply_text(f"❌ Todo #{tid} not found.")

        else:
            await update.message.reply_text("📝 *Todo Commands*\n\n/todo — List all\n/todo add <task> — Add\n/todo done <id> — Toggle done\n/todo del <id> — Delete")

    except Exception as e:
        logger.error(f"Todo error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Todo operation failed.")
        except Exception:
            pass


# ── Notes ──

async def note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        args = context.args if context.args else []
        if not args:
            # Show notes
            notes = db.get_notes(user_id)
            if not notes:
                await update.message.reply_text("📒 *Your Notes* — empty!\n\nUse /note add <title> <content> to save notes.")
                return
            text = "📒 *Your Notes*\n\n"
            for n in notes:
                text += f"📄 [{n['id']}] *{n['title']}*\n{n['content'][:80]}{'...' if len(n['content']) > 80 else ''}\n\n"
            text += "/note add <title> <content> — Save\n/note get <id> — Read full\n/note del <id> — Delete"
            await safe_reply(update, text)
            return

        action = args[0].lower()

        if action == "add":
            rest = " ".join(args[1:])
            if not rest:
                await update.message.reply_text("❌ Usage: /note add <title> | <content>")
                return
            if "|" in rest:
                parts = rest.split("|", 1)
                title = parts[0].strip()
                content = parts[1].strip()
            else:
                title = rest[:30]
                content = rest
            nid = db.save_note(user_id, title, content)
            await update.message.reply_text(f"📄 Note saved! (ID: {nid})\n\n*{title}*")

        elif action == "get":
            if len(args) < 2:
                await update.message.reply_text("❌ Provide ID: /note get <id>")
                return
            nid = int(args[1])
            note = db.get_note(user_id, nid)
            if note:
                await safe_reply(update, f"📄 *{note['title']}*\n\n{note['content']}")
            else:
                await update.message.reply_text(f"❌ Note #{nid} not found.")

        elif action == "del":
            if len(args) < 2:
                await update.message.reply_text("❌ Provide ID: /note del <id>")
                return
            nid = int(args[1])
            if db.delete_note(user_id, nid):
                await update.message.reply_text(f"🗑️ Deleted note #{nid}")
            else:
                await update.message.reply_text(f"❌ Note #{nid} not found.")

        else:
            await update.message.reply_text("📒 *Note Commands*\n\n/note — List all\n/note add <title> | <content>\n/note get <id> — Read\n/note del <id> — Delete")

    except Exception as e:
        logger.error(f"Note error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Note operation failed.")
        except Exception:
            pass


# ── Memory ──

async def remember_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        args = context.args if context.args else []
        if not args:
            await update.message.reply_text("🧠 Usage: /remember <key> <value>\n\nExample: /remember favcolor blue")
            return

        # Check for delete
        if args[0].lower() == "delete":
            key = " ".join(args[1:])
            if not key:
                await update.message.reply_text("❌ Usage: /remember delete <key>")
                return
            if db.delete_memory(user_id, key):
                await update.message.reply_text(f"🗑️ Forgot: {key}")
            else:
                await update.message.reply_text(f"❌ No memory found: {key}")
            return

        # key = first word, value = rest
        key = args[0]
        value = " ".join(args[1:])
        if not value:
            await update.message.reply_text("❌ Provide a value: /remember <key> <value>")
            return

        db.save_memory(user_id, key, value)
        await update.message.reply_text(f"🧠 Remembered!\n\n*{key}* = {value}")

    except Exception as e:
        logger.error(f"Remember error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Memory operation failed.")
        except Exception:
            pass


async def memories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        memories = db.get_memories(user_id)
        if not memories:
            await update.message.reply_text("🧠 *No memories yet!*\n\nUse /remember <key> <value> to save things I should remember.")
            return

        text = "🧠 *My Memories About You*\n\n"
        for m in memories:
            text += f"• *{m['key']}* = {m['value']}\n"
        text += "\n/remember delete <key> — Forget something"
        await safe_reply(update, text)

    except Exception as e:
        logger.error(f"Memories error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Could not retrieve memories.")
        except Exception:
            pass


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = safe_get_user_id(update)
    try:
        if user_id == 0:
            await update.message.reply_text("❌ Could not identify user.")
            return

        if db.clear_history(user_id):
            await update.message.reply_text("🧹 Chat history cleared! Fresh start. 🎉")
        else:
            await update.message.reply_text("❌ Nothing to clear.")

    except Exception as e:
        logger.error(f"Clear error (uid={user_id}): {e}")
        try:
            await update.message.reply_text("❌ Failed to clear history.")
        except Exception:
            pass


# ═══════════════════════════════════════════════════
# GLOBAL ERROR HANDLER
# Extra safe — doesn't rely on any variable being defined.
# ═══════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all uncaught errors."""
    # Extract user_id as safely as possible
    uid = 0
    try:
        if update and hasattr(update, 'effective_user') and update.effective_user:
            uid = update.effective_user.id
        elif update and hasattr(update, 'message') and update.message and update.message.from_user:
            uid = update.message.from_user.id
        elif update and hasattr(update, 'callback_query') and update.callback_query and update.callback_query.from_user:
            uid = update.callback_query.from_user.id
    except Exception:
        pass

    error = context.error if context and hasattr(context, 'error') else "Unknown error"
    logger.error(f"Unhandled error (uid={uid}): {error}")

    # Try to notify user
    try:
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text("⚠️ Something went wrong. Please try again!")
        elif update and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer("Something went wrong!", show_alert=True)
    except Exception:
        pass


# ═══════════════════════════════════════════════════
# BOT SETUP & REGISTRATION
# ═══════════════════════════════════════════════════

def setup_bot():
    """Create and configure the Telegram bot application."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register error handler FIRST
    application.add_error_handler(error_handler)

    # Command handlers — ALL features
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))

    # AI & Search
    application.add_handler(CommandHandler("search", search_cmd))
    application.add_handler(CommandHandler("news", news_cmd))
    application.add_handler(CommandHandler("image", image_cmd))
    application.add_handler(CommandHandler("code", code_cmd))
    application.add_handler(CommandHandler("debug", debug_cmd))
    application.add_handler(CommandHandler("explain", explain_cmd))
    application.add_handler(CommandHandler("flashcards", flashcards_cmd))
    application.add_handler(CommandHandler("quiz", quiz_cmd))
    application.add_handler(CommandHandler("translate", translate_cmd))
    application.add_handler(CommandHandler("summarize_url", summarize_url_cmd))
    application.add_handler(CommandHandler("summarize", summarize_cmd))
    application.add_handler(CommandHandler("rewrite", rewrite_cmd))
    application.add_handler(CommandHandler("compare", compare_cmd))
    application.add_handler(CommandHandler("story", story_cmd))
    application.add_handler(CommandHandler("poem", poem_cmd))
    application.add_handler(CommandHandler("math", math_cmd))

    # Text Tools
    application.add_handler(CommandHandler("calc", calc_cmd))
    application.add_handler(CommandHandler("define", define_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("case", case_cmd))
    application.add_handler(CommandHandler("reverse", reverse_cmd))
    application.add_handler(CommandHandler("synonym", synonym_cmd))
    application.add_handler(CommandHandler("antonym", antonym_cmd))
    application.add_handler(CommandHandler("emojify", emojify_cmd))
    application.add_handler(CommandHandler("lorem", lorem_cmd))
    application.add_handler(CommandHandler("repeat", repeat_cmd))

    # Encoding & Crypto
    application.add_handler(CommandHandler("morse", morse_cmd))
    application.add_handler(CommandHandler("binary", binary_cmd))
    application.add_handler(CommandHandler("hash", hash_cmd))
    application.add_handler(CommandHandler("base64", base64_cmd))
    application.add_handler(CommandHandler("password", password_cmd))
    application.add_handler(CommandHandler("pstrength", pstrength_cmd))
    application.add_handler(CommandHandler("emailcheck", emailcheck_cmd))

    # Converters
    application.add_handler(CommandHandler("currency", currency_cmd))
    application.add_handler(CommandHandler("unit", unit_cmd))
    application.add_handler(CommandHandler("color", color_cmd))
    application.add_handler(CommandHandler("randomcolor", randomcolor_cmd))
    application.add_handler(CommandHandler("roman", roman_cmd))

    # Calculators
    application.add_handler(CommandHandler("bmi", bmi_cmd))
    application.add_handler(CommandHandler("tip", tip_cmd))
    application.add_handler(CommandHandler("percentage", percentage_cmd))
    application.add_handler(CommandHandler("age", age_cmd))
    application.add_handler(CommandHandler("datediff", datediff_cmd))

    # Info & Lookup
    application.add_handler(CommandHandler("timezone", timezone_cmd))
    application.add_handler(CommandHandler("country", country_cmd))
    application.add_handler(CommandHandler("element", element_cmd))
    application.add_handler(CommandHandler("iplookup", iplookup_cmd))

    # Fun & Games
    application.add_handler(CommandHandler("coinflip", coinflip_cmd))
    application.add_handler(CommandHandler("dice", dice_cmd))
    application.add_handler(CommandHandler("random", random_cmd))
    application.add_handler(CommandHandler("rps", rps_cmd))
    application.add_handler(CommandHandler("roulette", roulette_cmd))
    application.add_handler(CommandHandler("riddle", riddle_cmd))
    application.add_handler(CommandHandler("trivia", trivia_cmd))
    application.add_handler(CommandHandler("tod", tod_cmd))
    application.add_handler(CommandHandler("wyr", wyr_cmd))

    # Fun Content
    application.add_handler(CommandHandler("joke", joke_cmd))
    application.add_handler(CommandHandler("quote", quote_cmd))
    application.add_handler(CommandHandler("fact", fact_cmd))
    application.add_handler(CommandHandler("compliment", compliment_cmd))
    application.add_handler(CommandHandler("advice", advice_cmd))
    application.add_handler(CommandHandler("pickupline", pickupline_cmd))
    application.add_handler(CommandHandler("motivation", motivation_cmd))

    # Productivity
    application.add_handler(CommandHandler("todo", todo_cmd))
    application.add_handler(CommandHandler("note", note_cmd))
    application.add_handler(CommandHandler("remember", remember_cmd))
    application.add_handler(CommandHandler("memories", memories_cmd))
    application.add_handler(CommandHandler("clear", clear_cmd))

    # Message handler — catches all text that isn't a command
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    return application


# ═══════════════════════════════════════════════════
# MAIN — Flask + Telegram Bot in background thread
# ═══════════════════════════════════════════════════

def run_bot():
    """Run the Telegram bot in its own event loop (called from thread)."""
    try:
        application = setup_bot()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def bot_main():
            logger.info("Initializing Telegram bot...")
            await application.initialize()
            logger.info("Starting Telegram bot polling...")
            await application.updater.start_polling(drop_pending_updates=True)
            await application.start()
            logger.info("Bot is running!")
            # Keep running forever
            while True:
                await asyncio.sleep(3600)

        logger.info("Starting bot coroutine...")
        loop.run_until_complete(bot_main())
    except Exception as e:
        logger.error(f"Bot thread error: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("AgentX Bot v2.0 — Starting up")
    logger.info("=" * 50)

    # Initialize database
    db.init_db()
    logger.info("Database initialized.")

    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started.")

    # Give bot time to initialize
    import time
    time.sleep(5)

    # Start Flask server in main thread (required for Render)
    logger.info(f"Starting Flask health server on port {PORT}...")
    flask_app.run(host="0.0.0.0", port=PORT)
