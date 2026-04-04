"""
AgentX v2 - Your free AI agent on Telegram.
Runs on Render free tier forever. No API keys needed.
"""
import os
import sys
import json
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

print("AgentX v2 starting...", flush=True)

from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

import ai
import db as database
import tools

BOT_TOKEN = os.getenv("BOT_TOKEN", "8697860970:AAG-4ZKF5y-Rsmm7pxNUPv5pbLURtwe5uYI")

# Initialize DB RIGHT HERE at startup (not in a thread!)
print("Initializing database...", flush=True)
db = database.DB()
print("Database ready!", flush=True)

SYSTEM_PROMPT = """You are AgentX, a powerful AI assistant on Telegram.
Be direct and useful. Use markdown formatting. Help with anything."""

WELCOME = """Welcome to AgentX! Your free AI assistant.

Just type anything to chat, or use commands:

/search - Web search
/image - Generate images
/code - Generate code
/debug - Fix bugs
/explain - Explain code
/flashcards - Create flashcards
/quiz - Take a quiz
/summarize - Summarize URL
/analyze - Deep analysis
/translate - Translate text
/calc - Math solver
/define - Dictionary
/password - Generate password
/joke - Random joke
/quote - Inspirational quote
/fact - Random fact
/rewrite - Rewrite text
/compare - Compare things
/remember - Save memory
/memories - View memories
/forget - Delete memory
/clear - Clear history
/end - End topic
/help - All commands"""

HELP = """AgentX v2 - Commands:

CHAT: Just type anything
/search query - Web search
/news topic - Latest news
/analyze topic - Deep analysis

CREATIVE:
/image prompt - Generate image
/rewrite text | style - Rewrite

CODING:
/code task - Generate code
/debug code - Fix bugs
/explain code - Explain

LEARNING:
/flashcards topic - Flashcards
/quiz topic - Quiz
/summarize url - Summarize page

TOOLS:
/translate text | lang - Translate
/define word - Dictionary
/calc expression - Math
/password - Random password
/compare A vs B - Compare

FUN:
/joke - Random joke
/quote - Inspirational quote
/fact - Random fact

MEMORY:
/remember key = value
/memories
/forget key

OTHER:
/history - Chat history
/clear - Clear history
/end - End topic"""


def process(uid, text):
    """Process message and return response string."""
    text = text.strip()

    if not text.startswith("/"):
        return None

    parts = text.split(None, 1)
    cmd = parts[0].lstrip("/").lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "start": return WELCOME
    if cmd == "help": return HELP

    if cmd == "clear":
        db.clear_history(uid)
        return "History cleared!"

    if cmd == "end":
        db.clear_history(uid)
        return "Topic ended! Fresh start."

    if cmd == "history":
        msgs = db.get_history(uid, 20)
        if not msgs: return "No history yet."
        return "\n".join(f"{'You' if m['role']=='user' else 'Bot'}: {m['content'][:100]}" for m in msgs)

    if cmd == "search":
        if not args: return "Usage: /search <query>"
        return tools.search_and_summarize(args)

    if cmd == "news":
        if not args: return "Usage: /news <topic>"
        return tools.search_and_summarize(f"{args} news today")

    if cmd == "image":
        if not args: return "Usage: /image <description>"
        url = tools.generate_image(args)
        if url: return "IMAGE:" + url + ":" + args
        return "Failed to generate image."

    if cmd == "code":
        if not args: return "Usage: /code <task>"
        return ai.chat(f"Write code for: {args}", system_msg="You are an expert programmer. Provide complete runnable code.")

    if cmd == "debug":
        if not args: return "Usage: /debug <paste code>"
        return ai.chat(f"Find and fix bugs:\n```\n{args}\n```", system_msg="You are an expert debugger.")

    if cmd == "explain":
        if not args: return "Usage: /explain <paste code>"
        return ai.chat(f"Explain this code:\n```\n{args}\n```", system_msg="You are a coding teacher.")

    if cmd == "flashcards" or cmd == "flashcard":
        if not args:
            cards = db.get_flashcards(uid)
            if not cards: return "No flashcards. Create: /flashcards <topic>"
            return "\n".join(f"Q: {c['front']}\nA: {c['back']}" for c in cards[-15:])
        cards = tools.make_flashcards(args)
        if cards:
            db.save_flashcards(uid, args, [(c["front"], c["back"]) for c in cards])
            return tools.format_flashcards(cards)
        return "Failed to generate flashcards."

    if cmd == "quiz":
        if not args:
            quizzes = db.get_quizzes(uid)
            if not quizzes: return "No quizzes. Create: /quiz <topic>"
            return "\n".join(f"- {q['topic']}" for q in quizzes)
        questions = tools.make_quiz(args)
        if questions:
            db.save_quiz(uid, args, questions)
            return tools.format_quiz(questions)
        return "Failed to generate quiz."

    if cmd == "summarize":
        urls = tools.extract_urls(args)
        if not urls: return "Usage: /summarize <url>"
        scraped = tools.scrape_url(urls[0])
        if "error" in scraped: return f"Error: {scraped['error']}"
        return ai.chat(f"Summarize:\n{scraped['text'][:10000]}", system_msg="Provide a clear summary with bullet points.")

    if cmd == "summarize_text":
        if not args: return "Usage: /summarize_text <paste text>"
        return tools.summarize_text(args)

    if cmd == "analyze":
        if not args: return "Usage: /analyze <topic>"
        return ai.chat(f"Deep analysis of: {args}\nProvide: Overview, Key Insights, Pros, Cons, Recommendations.", system_msg="You are an expert analyst.")

    if cmd == "translate":
        if not args: return "Usage: /translate text | language"
        parts2 = args.rsplit("|", 1)
        lang = parts2[1].strip() if len(parts2) == 2 else "English"
        txt = parts2[0].strip()
        return tools.translate(txt, lang)

    if cmd == "calc":
        if not args: return "Usage: /calc <expression>"
        return tools.calc(args)

    if cmd == "define":
        if not args: return "Usage: /define <word>"
        return tools.define(args)

    if cmd == "password":
        try: length = max(8, min(int(args.strip()), 64))
        except: length = 16
        return f"Generated password ({length} chars):\n{tools.gen_password(length)}"

    if cmd == "joke": return tools.random_joke()
    if cmd == "quote": return tools.random_quote()
    if cmd == "fact": return tools.random_fact()

    if cmd == "rewrite":
        if not args: return "Usage: /rewrite text | style"
        parts2 = args.rsplit("|", 1)
        style = parts2[1].strip() if len(parts2) == 2 else "better"
        return tools.rewrite_text(parts2[0].strip(), style)

    if cmd == "compare":
        if not args: return "Usage: /compare A vs B"
        return tools.compare_things(args)

    if cmd == "remember":
        if not args or "=" not in args: return "Usage: /remember key = value"
        k, v = args.split("=", 1)
        db.save_memory(uid, k.strip(), v.strip())
        return f"Remembered: {k.strip()} = {v.strip()}"

    if cmd == "memories":
        mems = db.get_memories(uid)
        if not mems: return "No memories. Save: /remember key = value"
        return "\n".join(f"- {k}: {v}" for k, v in mems.items())

    if cmd == "forget":
        if not args: return "Usage: /forget <key>"
        db.delete_memory(uid, args.strip())
        return f"Forgot: {args.strip()}"

    return None


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle every message."""
    try:
        user = update.effective_user
        text = (update.message.text or "").strip()
        if not text:
            return

        # Save user (don't let this crash anything)
        try:
            db.save_user(user.id, user.username or "", user.first_name or "")
        except Exception as e:
            print(f"[DB Warning] {e}", flush=True)

        # Try command
        result = process(user.id, text)

        # If not a command, do AI chat
        if result is None:
            urls = tools.extract_urls(text)
            if urls:
                scraped = tools.scrape_url(urls[0])
                if "error" not in scraped:
                    result = ai.chat(
                        f"User said: {text}\nPage: {scraped['title']}\n{scraped['text'][:8000]}",
                        system_msg=SYSTEM_PROMPT,
                    )
                else:
                    result = ai.chat(text, system_msg=SYSTEM_PROMPT)
            else:
                mems = db.get_memories(user.id)
                sp = SYSTEM_PROMPT
                if mems:
                    sp += "\nYou know about user: " + json.dumps(mems)
                hist = db.get_history(user.id, 12)
                result = ai.chat(text, system_msg=sp, history=hist)

        if not result:
            return

        # Save to history (don't let this crash)
        try:
            db.save_msg(user.id, "user", text[:2000])
            db.save_msg(user.id, "assistant", result[:2000])
        except Exception as e:
            print(f"[DB Warning] {e}", flush=True)

        # Handle image
        if result.startswith("IMAGE:"):
            parts = result.split(":", 2)
            if len(parts) >= 3:
                url, caption = parts[1], parts[2]
                try:
                    await update.message.reply_photo(photo=url, caption=f"Generated: {caption}")
                    return
                except Exception:
                    await update.message.reply_text(f"Generated: {caption}\n{url}")
                    return

        # Send text - use HTML (never fails)
        for chunk in tools.split_text(result, 4000):
            try:
                await update.message.reply_text(chunk)
            except Exception:
                try:
                    await update.message.reply_text(chunk, parse_mode="Markdown")
                except Exception:
                    await update.message.reply_text("Could not send response. Try again.")

    except Exception as e:
        print(f"[Error] {e}", flush=True)
        traceback.print_exc()
        try:
            await update.message.reply_text(f"Error: {e}")
        except Exception:
            pass


async def err_handler(update, context):
    print(f"[Bot Error] {context.error}", flush=True)


def run_bot():
    """Run Telegram bot in its own event loop."""
    import asyncio

    async def loop():
        print("[Bot] Building app...", flush=True)
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.ALL, handler))
        app.add_error_handler(err_handler)

        # Set menu
        try:
            import httpx
            httpx.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands",
                json={"commands": [
                    {"command": "start", "description": "Start"},
                    {"command": "help", "description": "Commands"},
                    {"command": "search", "description": "Search web"},
                    {"command": "image", "description": "Make image"},
                    {"command": "code", "description": "Write code"},
                ]},
                timeout=10,
            )
        except Exception:
            pass

        print("[Bot] Starting polling...", flush=True)

        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            print("[Bot] AgentX is RUNNING!", flush=True)
            while True:
                await asyncio.sleep(3600)

    asyncio.run(loop())


class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"AgentX v2 is alive!")
    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("=" * 40, flush=True)
    print("  AgentX v2 - Starting", flush=True)
    print("=" * 40, flush=True)

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheck)
    print(f"[Server] Port {port}", flush=True)
    server.serve_forever()
