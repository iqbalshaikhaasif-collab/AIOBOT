"""
AgentX v2 — Complete Rewrite
Your free AI agent on Telegram. Runs on Render free tier forever.

Features (20):
  1. AI Chat           11. Translate
  2. Web Search        12. Calculator
  3. News              13. Dictionary
  4. Image Generation  14. Password Gen
  5. Code Generation   15. Joke
  6. Code Debug        16. Quote
  7. Code Explain      17. Fun Fact
  8. Flashcards        18. Rewrite Text
  9. Quiz              19. Compare Things
  10. Summarize        20. Word Count
  + Memory system + URL analysis + Deep analysis

Architecture:
  - HTTP server on PORT (main process — keeps Render alive)
  - Telegram bot in background thread
  - Pollinations.ai (free, no key)
  - SQLite database
"""
import os
import sys
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# ━━━ Print logs to stdout (Render needs this) ━━━━━
print("AgentX v2 starting...", flush=True)

from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

import ai
import db as database
import tools

# ━━━ Config ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.getenv("BOT_TOKEN", "8697860970:AAG-4ZKF5y-Rsmm7pxNUPv5pbLURtwe5uYI")

SYSTEM_PROMPT = """You are AgentX — a powerful, friendly AI assistant on Telegram.

You can help with anything: questions, coding, research, learning, writing, math, and more.

Style:
- Be direct and useful, no fluff
- Use markdown: **bold**, *italic*, `code`, ```code blocks```
- Add relevant emojis sparingly
- Give specific, actionable answers
- If unsure, say so honestly
- Ask follow-up questions when helpful"""

WELCOME_MSG = """Welcome to AgentX! Your free AI agent.

Just type anything and I'll help. Or use commands:

/search query - Web search
/news topic - Latest news
/image prompt - Generate images
/code task - Generate code
/debug code - Fix bugs
/explain code - Explain code
/flashcards topic - Create flashcards
/quiz topic - Take a quiz
/summarize url - Summarize webpage
/summarize_text paste - Summarize pasted text
/analyze topic - Deep analysis
/translate text | lang - Translate
/calc expression - Solve math
/define word - Get definition
/password - Generate password
/joke - Random joke
/quote - Inspirational quote
/fact - Random fact
/rewrite text | style - Rewrite text
/compare A vs B - Compare things
/remember key = value - Save memory
/memories - View memories
/forget key - Delete memory
/clear - Clear chat history
/end - End current topic
/help - All commands"""

HELP_MSG = """AgentX v2 - All Commands

CHAI & AI:
- Just type anything for AI chat
/history - View chat history
/clear - Clear history

SEARCH & RESEARCH:
/search query - Web search
/news topic - Latest news
/analyze topic - Deep analysis

CREATIVE:
/image prompt - Generate images
/rewrite text | style - Rewrite text

CODING:
/code task - Generate code
/debug code - Fix bugs
/explain code - Explain code

LEARNING:
/flashcards topic - Flashcards
/quiz topic - Take quiz
/summarize url - Summarize webpage
/summarize_text text - Summarize text

LANGUAGES:
/translate text | language - Translate
/define word - Dictionary lookup

MATH & TOOLS:
/calc expression - Math solver
/password [length] - Password generator
/compare A vs B - Compare things

FUN:
/joke - Random joke
/quote - Inspirational quote
/fact - Random fact

MEMORY:
/remember key = value - Save
/memories - View all
/forget key - Delete

Everything is 100% free!"""

# ━━━ Globals ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
db = None


# ━━━ Helpers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def safe_send(update, text, parse_mode="Markdown"):
    """Send a message safely, handling Telegram limits and errors."""
    try:
        chunks = tools.split_text(text, 4000)
        for chunk in chunks:
            try:
                update.message.reply_text(
                    chunk,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                )
            except Exception:
                # Fallback without markdown if formatting fails
                update.message.reply_text(chunk, disable_web_page_preview=True)
    except Exception:
        pass


def parse_cmd(text):
    """Parse /command args. Returns (cmd, args) or None."""
    text = text.strip()
    if not text.startswith("/"):
        return None
    parts = text.split(None, 1)
    cmd = parts[0].lstrip("/").lower()
    args = parts[1] if len(parts) > 1 else ""
    return (cmd, args)


# ━━━ Command Router ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_command(user_id, text, username):
    """Process a command and return response text."""
    cmd = parse_cmd(text)
    if not cmd:
        return None

    name, args = cmd

    # ── Welcome & Help ──
    if name == "start":
        return WELCOME_MSG

    if name == "help":
        return HELP_MSG

    # ── History ──
    if name == "history":
        msgs = db.get_history(user_id, 30)
        if not msgs:
            return "No history yet. Start chatting!"
        out = ""
        for m in msgs:
            icon = "You" if m["role"] == "user" else "Bot"
            out += f"{icon}: {m['content'][:120]}\n\n"
        return out

    if name == "clear":
        db.clear_history(user_id)
        return "History cleared!"

    if name == "end":
        db.clear_history(user_id)
        return "Topic ended! Fresh start. Send me anything to begin a new conversation."

    # ── Search ──
    if name == "search":
        if not args:
            return "Usage: /search <query>\nExample: /search best Python frameworks 2025"
        return tools.search_and_summarize(args)

    # ── News ──
    if name == "news":
        if not args:
            return "Usage: /news <topic>\nExample: /news artificial intelligence"
        return tools.search_and_summarize(f"{args} latest news today")

    # ── Image Generation ──
    if name == "image":
        if not args:
            return "Usage: /image <description>\nExample: /image a cat riding a skateboard"
        url = tools.generate_image(args)
        if url:
            db.save_msg(user_id, "user", f"/image {args}")
            db.save_msg(user_id, "assistant", f"[Image: {args}]")
            return f"IMAGE:{url}:{args}"
        return "Failed to generate image. Try again."

    # ── Code Generation ──
    if name == "code":
        if not args:
            return "Usage: /code <what to build>\nExample: /code a Python web scraper"
        resp = ai.chat(
            f"Write clean, well-commented code for: {args}\n\nInclude imports, a working implementation, and example usage.",
            system_msg="You are an expert programmer. Provide complete, runnable code in appropriate language."
        )
        db.save_msg(user_id, "user", f"/code {args}")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Code Generated:*\n\n{resp}"

    # ── Code Debug ──
    if name == "debug":
        if not args:
            return "Usage: /debug <paste your code>\n\nOptionally add error message after."
        resp = ai.chat(
            f"Find and fix bugs in this code:\n\n```\n{args}\n```",
            system_msg="You are an expert debugger. Find all bugs, explain them, and provide fixed code."
        )
        db.save_msg(user_id, "user", "/debug")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Bug Fix:*\n\n{resp}"

    # ── Code Explain ──
    if name == "explain":
        if not args:
            return "Usage: /explain <paste code>"
        resp = ai.chat(
            f"Explain this code clearly:\n\n```\n{args}\n```",
            system_msg="You are a coding teacher. Explain code step by step in simple terms."
        )
        db.save_msg(user_id, "user", "/explain")
        db.save_msg(user_id, "assistant", resp[:2000])
        return resp

    # ── Flashcards ──
    if name == "flashcard" or name == "flashcards":
        if not args:
            cards = db.get_flashcards(user_id)
            if not cards:
                return "No saved flashcards.\n\nCreate: /flashcards <topic>"
            out = "*Your Flashcards:*\n\n"
            for i, c in enumerate(cards[-20:], 1):
                out += f"{i}. *Q:* {c['front']}\n   *A:* {c['back']}\n\n"
            return out
        cards = tools.make_flashcards(args)
        if cards:
            db.save_flashcards(user_id, args, [(c["front"], c["back"]) for c in cards])
            db.save_msg(user_id, "user", f"/flashcards {args}")
            db.save_msg(user_id, "assistant", f"Generated {len(cards)} cards")
            return tools.format_flashcards(cards)
        return "Couldn't generate flashcards. Try again."

    # ── Quiz ──
    if name == "quiz":
        if not args:
            quizzes = db.get_quizzes(user_id)
            if not quizzes:
                return "No past quizzes.\n\nCreate: /quiz <topic>"
            out = "*Past Quizzes:*\n\n"
            for q in quizzes:
                out += f"- {q['topic']} (score: {q['score'] or 'pending'})\n"
            return out
        questions = tools.make_quiz(args)
        if questions:
            db.save_quiz(user_id, args, questions)
            db.save_msg(user_id, "user", f"/quiz {args}")
            db.save_msg(user_id, "assistant", f"Quiz: {len(questions)} questions")
            return tools.format_quiz(questions)
        return "Couldn't generate quiz. Try again."

    # ── Summarize URL ──
    if name == "summarize":
        urls = tools.extract_urls(args)
        if not urls:
            return "Usage: /summarize <url>\nExample: /summarize https://example.com/article"
        scraped = tools.scrape_url(urls[0])
        if "error" in scraped:
            return f"Couldn't access that URL: {scraped['error']}"
        resp = ai.chat(
            f"Summarize this article:\n\nTitle: {scraped['title']}\n\n{scraped['text'][:10000]}",
            system_msg="Provide a clear summary with key points. Use bullet points."
        )
        db.save_msg(user_id, "user", f"/summarize {urls[0]}")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Summary: {scraped['title']}*\n\n{resp}"

    # ── Summarize Text ──
    if name == "summarize_text":
        if not args:
            return "Usage: /summarize_text <paste your long text here>"
        resp = tools.summarize_text(args)
        db.save_msg(user_id, "user", "/summarize_text")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Summary:*\n\n{resp}"

    # ── Deep Analysis ──
    if name == "analyze":
        if not args:
            return "Usage: /analyze <topic or URL>"
        urls = tools.extract_urls(args)
        if urls:
            scraped = tools.scrape_url(urls[0])
            if "error" not in scraped:
                args = f"Analyze this:\n\n{scraped['text'][:8000]}"
        resp = ai.chat(
            f"Perform deep analysis:\n\n{args}\n\nProvide: Overview, Key Insights, Pros, Cons, Recommendations, Conclusion.",
            system_msg="You are an expert analyst. Be thorough and specific."
        )
        db.save_msg(user_id, "user", "/analyze")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Deep Analysis:*\n\n{resp}"

    # ── Translate ──
    if name == "translate":
        if not args:
            return "Usage: /translate <text> | <language>\n\nExample: /translate Hello world | Spanish"
        parts = args.rsplit("|", 1)
        if len(parts) == 2:
            text_to_translate = parts[0].strip()
            lang = parts[1].strip()
        else:
            text_to_translate = args
            lang = "English"
        resp = tools.translate(text_to_translate, lang)
        db.save_msg(user_id, "user", "/translate")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Translation ({lang}):*\n\n{resp}"

    # ── Calculator ──
    if name == "calc":
        if not args:
            return "Usage: /calc <expression>\n\nExamples:\n/calc 15 * 23 + 7\n/calc solve x^2 - 5x + 6 = 0"
        resp = tools.calc(args)
        db.save_msg(user_id, "user", f"/calc {args}")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Result:*\n\n{resp}"

    # ── Dictionary ──
    if name == "define":
        if not args:
            return "Usage: /define <word>\nExample: /define serendipity"
        resp = tools.define(args)
        db.save_msg(user_id, "user", f"/define {args}")
        db.save_msg(user_id, "assistant", resp[:2000])
        return resp

    # ── Password ──
    if name == "password":
        try:
            length = int(args.strip()) if args.strip() else 16
            length = max(8, min(length, 64))
        except ValueError:
            length = 16
        pw = tools.gen_password(length)
        return f"*Generated Password ({length} chars):*\n\n`{pw}`\n\n_Don't share this with anyone!_"

    # ── Joke ──
    if name == "joke":
        return tools.random_joke()

    # ── Quote ──
    if name == "quote":
        return tools.random_quote()

    # ── Fact ──
    if name == "fact":
        return tools.random_fact()

    # ── Rewrite ──
    if name == "rewrite":
        if not args:
            return "Usage: /rewrite <text> | <style>\n\nStyles: professional, casual, academic, simple, creative\n\nExample: /rewrite Hello I want job | professional"
        parts = args.rsplit("|", 1)
        if len(parts) == 2:
            text_rw = parts[0].strip()
            style = parts[1].strip()
        else:
            text_rw = args
            style = "better"
        resp = tools.rewrite_text(text_rw, style)
        db.save_msg(user_id, "user", "/rewrite")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Rewritten ({style}):*\n\n{resp}"

    # ── Compare ──
    if name == "compare":
        if not args:
            return "Usage: /compare <A> vs <B>\n\nExample: /compare Python vs JavaScript"
        resp = tools.compare_things(args)
        db.save_msg(user_id, "user", f"/compare {args}")
        db.save_msg(user_id, "assistant", resp[:2000])
        return f"*Comparison:*\n\n{resp}"

    # ── Memory ──
    if name == "remember":
        if not args or "=" not in args:
            return "Usage: /remember <key> = <value>\n\nExample: /remember name = Iqbal"
        key, value = args.split("=", 1)
        db.save_memory(user_id, key.strip(), value.strip())
        return f"Remembered!\n*{key.strip()}* = {value.strip()}"

    if name == "memories":
        mems = db.get_memories(user_id)
        if not mems:
            return "No memories saved.\n\nSave: /remember key = value"
        out = "*Your Memories:*\n\n"
        for k, v in mems.items():
            out += f"- *{k}*: {v}\n"
        return out

    if name == "forget":
        if not args:
            return "Usage: /forget <key>\n\nView: /memories"
        db.delete_memory(user_id, args.strip())
        return f"Forgot about *{args.strip()}*."

    return None


# ━━━ Telegram Handlers ━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages."""
    try:
        user = update.effective_user
        text = update.message.text or ""
        if not text.strip():
            return

        db.save_user(user.id, user.username or "", user.first_name or "")
        await update.message.chat.send_action("typing")

        # Try command first
        result = process_command(user.id, text, user.username or "")

        if result is None:
            # Not a command — check for URLs in message
            urls = tools.extract_urls(text)
            if urls:
                scraped = tools.scrape_url(urls[0])
                if "error" not in scraped:
                    result = ai.chat(
                        f"The user said: {text}\n\nThey shared this URL. Page content:\nTitle: {scraped['title']}\n\n{scraped['text'][:10000]}\n\nHelp them with whatever they need about this content.",
                        system_msg=SYSTEM_PROMPT,
                        history=db.get_history(user.id, 16),
                    )
                else:
                    result = ai.chat(text, system_msg=SYSTEM_PROMPT, history=db.get_history(user.id, 16))
            else:
                # Regular AI chat
                memories = db.get_memories(user.id)
                sys_prompt = SYSTEM_PROMPT
                if memories:
                    sys_prompt += f"\n\nUser facts you know: {json.dumps(memories)}"
                result = ai.chat(text, system_msg=sys_prompt, history=db.get_history(user.id, 16))

        if result:
            # Handle image responses
            if result.startswith("IMAGE:"):
                parts = result.split(":", 3)
                if len(parts) >= 4:
                    url, caption = parts[1], parts[2] + ": " + parts[3]
                    try:
                        await update.message.reply_photo(
                            photo=url, caption=f"Generated: {caption}",
                        )
                    except Exception:
                        await update.message.reply_text(f"Generated: {caption}\n\n{url}")
                    db.save_msg(user_id, "user", text[:2000])
                    db.save_msg(user_id, "assistant", f"[Image: {caption}]")
                    return

            # Regular text response
            db.save_msg(user_id, "user", text[:2000])
            db.save_msg(user_id, "assistant", result[:2000])
            safe_send(update, result)

    except Exception as e:
        print(f"[Handler Error] {e}", flush=True)
        traceback.print_exc()
        try:
            await update.message.reply_text("Something went wrong. Please try again!")
        except Exception:
            pass


async def on_error(update, context):
    """Global error handler."""
    print(f"[Bot Error] {context.error}", flush=True)


# ━━━ Telegram Bot Thread ━━━━━━━━━━━━━━━━━━━━━━━━━

def run_bot():
    """Start the Telegram bot in its own event loop (thread-safe)."""
    import asyncio

    async def bot_loop():
        global db

        print("[Bot] Initializing...", flush=True)
        db = database.DB()
        print("[Bot] Database ready.", flush=True)

        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.ALL, on_message))
        app.add_error_handler(on_error)

        # Set bot menu
        try:
            import httpx
            httpx.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands",
                json={"commands": [
                    {"command": "start", "description": "Start bot"},
                    {"command": "help", "description": "All commands"},
                    {"command": "search", "description": "Search the web"},
                    {"command": "image", "description": "Generate image"},
                    {"command": "code", "description": "Generate code"},
                    {"command": "translate", "description": "Translate text"},
                    {"command": "flashcards", "description": "Create flashcards"},
                    {"command": "quiz", "description": "Take a quiz"},
                    {"command": "joke", "description": "Random joke"},
                    {"command": "calc", "description": "Math solver"},
                ]},
                timeout=10,
            )
        except Exception:
            pass

        print("[Bot] AgentX is running!", flush=True)

        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            # Keep the loop alive forever
            while True:
                await asyncio.sleep(3600)

    asyncio.run(bot_loop())


# ━━━ Health Check Server (Main Process) ━━━━━━━━━━━

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"AgentX v2 is alive!")

    def log_message(self, *a):
        pass  # Suppress noise


# ━━━ Entry Point ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("=" * 40, flush=True)
    print("  AgentX v2", flush=True)
    print("  Free forever. No API keys needed.", flush=True)
    print("=" * 40, flush=True)

    # Start Telegram bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # HTTP server as main process (Render requirement)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[Server] Health check on port {port}", flush=True)
    print("[Server] Ready!", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...", flush=True)
