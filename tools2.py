"""
tools2.py — Extended features for AgentX Bot (v2.0)
PDF, YouTube, Study Tools, Enhanced Writing, Coding, Research, Agent, Downloads.
"""

import os
import re
import json
import logging
import tempfile
from datetime import datetime

import requests
from ai import chat_single

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# SECTION 1: PDF PROCESSING
# ═══════════════════════════════════════════════════════════════

def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if i >= 30:  # Max 30 pages to avoid timeout
                    break
        return text.strip()
    except ImportError:
        return "__ERROR__: PyPDF2 not installed. Run: pip install PyPDF2"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return f"__ERROR__: {str(e)[:150]}"


def _check_pdf_error(text: str) -> str:
    """Return error message if PDF text has error, else empty string."""
    if text.startswith("__ERROR__:"):
        return text
    if len(text) < 30:
        return "❌ Could not extract enough text from PDF."
    return ""


def pdf_summary(text: str) -> str:
    """Generate smart summary from PDF content."""
    err = _check_pdf_error(text)
    if err:
        return err
    prompt = f"""Analyze this document thoroughly and provide:

1. **Smart Summary** — concise overview (2-3 paragraphs)
2. **Key Points** — bullet points of main takeaways
3. **Main Topics Covered** — listed

Document content (first part):
{text[:5000]}"""
    result = chat_single(prompt, "You are an expert document analyzer. Be thorough and well-structured.")
    return f"📄 *PDF Analysis*\n\n{result}"


def pdf_ask(text: str, question: str) -> str:
    """Answer a question about PDF content."""
    err = _check_pdf_error(text)
    if err:
        return err
    prompt = f"""Based ONLY on this document, answer the question accurately.

Document:
{text[:5000]}

Question: {question}"""
    return chat_single(prompt, "Answer based only on the document content. Cite specific parts when possible.")


def pdf_key_points(text: str) -> str:
    """Highlight key points from PDF."""
    err = _check_pdf_error(text)
    if err:
        return err
    prompt = f"""Extract and highlight the key points from this document.
Format as clear bullet points with brief explanations.

Document:
{text[:5000]}"""
    result = chat_single(prompt, "Extract the most important points. Use bullet points.")
    return f"🔑 *Key Points*\n\n{result}"


def pdf_flashcards(text: str) -> str:
    """Generate flashcards from PDF content."""
    err = _check_pdf_error(text)
    if err:
        return err
    prompt = f"""Create 8 educational flashcards from this document.
Format exactly like:
FRONT: [question or term]
BACK: [answer or definition]

Cover the most important concepts.

Document:
{text[:5000]}"""
    result = chat_single(prompt, "Create educational flashcards. Use exact FRONT:/BACK: format.")
    return f"📚 *Flashcards from PDF*\n\n{result}"


def pdf_quiz(text: str) -> str:
    """Generate quiz from PDF content."""
    err = _check_pdf_error(text)
    if err:
        return err
    prompt = f"""Create a 10-question MCQ quiz from this document.
Format:
Q1. [question]
a) ... b) ... c) ... d) ...
Answer: [correct letter]

Put ALL answers at the very end as an Answer Key.

Document:
{text[:5000]}"""
    result = chat_single(prompt, "Create a challenging quiz from the document. Answer key at end.")
    return f"📝 *Quiz from PDF*\n\n{result}"


def notes_to_flashcards(text: str) -> str:
    """Convert notes to flashcards."""
    prompt = f"""Convert these notes into 8 flashcards.
Format: FRONT: [question] | BACK: [answer]

Notes:
{text[:4000]}"""
    return chat_single(prompt, "Create flashcards from notes. Use FRONT:/BACK: format.")


def notes_to_quiz(text: str) -> str:
    """Convert notes to quiz."""
    prompt = f"""Create a 8-question MCQ quiz from these notes.
Format: Q1. [question]\na) ... b) ... c) ... d) ...\nAnswer: [letter]
Answer key at the end.

Notes:
{text[:4000]}"""
    return chat_single(prompt, "Create quiz from notes. MCQ with answer key at end.")


# ═══════════════════════════════════════════════════════════════
# SECTION 2: YOUTUBE PROCESSING
# ═══════════════════════════════════════════════════════════════

def _extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([\w-]{11})',
        r'(?:embed/)([\w-]{11})',
        r'(?:shorts/)([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _get_transcript(url: str) -> str:
    """Get transcript from YouTube video."""
    video_id = _extract_youtube_id(url)
    if not video_id:
        return "__ERROR__: Invalid YouTube URL. Use a youtube.com or youtu.be link."
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_list])
    except ImportError:
        return "__ERROR__: youtube-transcript-api not installed."
    except Exception as e:
        logger.error(f"Transcript error: {e}")
        return f"__ERROR__: Could not get transcript: {str(e)[:120]}"


def yt_summary(url: str) -> str:
    """Summarize YouTube video."""
    transcript = _get_transcript(url)
    if transcript.startswith("__ERROR__:"):
        return transcript
    prompt = f"""Summarize this YouTube video transcript thoroughly:
1. **Video Summary** (what the video is about, 2-3 paragraphs)
2. **Key Points** (main takeaways as bullet points)
3. **Important Details & Facts**

Transcript:
{transcript[:5000]}"""
    result = chat_single(prompt, "You are a video content analyzer. Provide clear, structured summaries.")
    return f"🎬 *YouTube Summary*\n\n{result}"


def yt_key_points(url: str) -> str:
    """Extract key points from YouTube video."""
    transcript = _get_transcript(url)
    if transcript.startswith("__ERROR__:"):
        return transcript
    prompt = f"""Extract the key points from this YouTube video as bullet points with brief explanations.

Transcript:
{transcript[:5000]}"""
    result = chat_single(prompt, "Extract key points as bullet points.")
    return f"🔑 *Video Key Points*\n\n{result}"


def yt_notes(url: str) -> str:
    """Generate study notes from YouTube video."""
    transcript = _get_transcript(url)
    if transcript.startswith("__ERROR__:"):
        return transcript
    prompt = f"""Convert this YouTube video transcript into well-organized study notes.
Use headings, subheadings, and bullet points. Make it easy to review.

Transcript:
{transcript[:5000]}"""
    result = chat_single(prompt, "Create well-structured study notes from video transcripts.")
    return f"📒 *Video Notes*\n\n{result}"


def yt_quiz(url: str) -> str:
    """Generate quiz from YouTube video."""
    transcript = _get_transcript(url)
    if transcript.startswith("__ERROR__:"):
        return transcript
    prompt = f"""Create an 8-question MCQ quiz from this YouTube video transcript.
Format: Q1. [question]\na) ... b) ... c) ... d) ...\nAnswer: [letter]
Put ALL answers at the very end.

Transcript:
{transcript[:5000]}"""
    result = chat_single(prompt, "Create quiz from video content. MCQ with answer key at end.")
    return f"📝 *Video Quiz*\n\n{result}"


# ═══════════════════════════════════════════════════════════════
# SECTION 3: STUDY TOOLS
# ═══════════════════════════════════════════════════════════════

def generate_study_plan(topics: str) -> str:
    """Generate personalized study plan."""
    prompt = f"""Create a detailed, personalized study plan for these topics: {topics}

Include:
1. **Weekly Breakdown** — what to study each week
2. **Daily Tasks** — specific daily goals
3. **Revision Schedule** — spaced repetition plan
4. **Practice Recommendations** — exercises and problems
5. **Resource Suggestions** — types of resources to use
6. **Milestones** — checkpoints to track progress"""
    result = chat_single(prompt, "You are an expert study planner. Create realistic, actionable study plans.")
    return f"📚 *Study Plan*\n\n{result}"


def generate_timetable(schedule_info: str) -> str:
    """Generate a structured timetable."""
    prompt = f"""Create a structured weekly timetable based on this info: {schedule_info}

Format as a clean table:
| Time | Mon | Tue | Wed | Thu | Fri | Sat | Sun |

Include time slots from morning to night. Be practical and include breaks."""
    result = chat_single(prompt, "Create clean, organized timetables in markdown table format.")
    return f"📅 *Timetable*\n\n{result}"


def current_affairs_summary() -> str:
    """Get daily current affairs summary."""
    news_text = ""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news("today top news world 2026", max_results=8))
        news_text = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')[:120]}" for r in results])
    except Exception as e:
        logger.error(f"Current affairs search error: {e}")

    prompt = f"""Create a daily current affairs summary from these news headlines.
Organize by category:
- 🌍 World News
- 💻 Technology
- 💼 Business & Economy
- 🔬 Science & Health
- 🏅 Sports

Use bullet points. Keep it concise but informative.

News:
{news_text}"""
    result = chat_single(prompt, "Create concise daily current affairs summaries organized by category.")
    return f"📰 *Daily Current Affairs*\n\n{result}"


# ═══════════════════════════════════════════════════════════════
# SECTION 4: ENHANCED WRITING TOOLS
# ═══════════════════════════════════════════════════════════════

def grammar_correct(text: str) -> str:
    """Correct grammar in text."""
    prompt = f"""Correct the grammar, spelling, punctuation, and style of this text.
Only output the corrected version. Explain major changes briefly at the end.

Original:
{text}"""
    return chat_single(prompt, "You are a grammar expert. Correct text and briefly explain major fixes.")


def simplify_text(text: str) -> str:
    """Simplify text — Explain Like I'm 5."""
    prompt = f"""Explain this in the simplest possible terms, as if explaining to a curious 12-year-old.
Use simple words, analogies, and examples. Break complex ideas into small parts.

Original:
{text}"""
    return chat_single(prompt, "Simplify complex text for easy understanding. Use analogies and simple words.")


def expand_notes(text: str) -> str:
    """Expand short notes into detailed answers."""
    prompt = f"""Expand these short notes into a comprehensive, detailed answer.
- Add explanations and context
- Include examples where helpful
- Maintain the original structure and meaning
- Make it suitable for an exam or assignment

Short notes:
{text}"""
    return chat_single(prompt, "Expand brief notes into detailed, well-structured answers with examples and context.")


def generate_essay(topic: str) -> str:
    """Generate a well-structured essay."""
    prompt = f"""Write a well-structured essay on: {topic}

Structure:
1. **Introduction** with a clear thesis statement
2. **3-4 Body Paragraphs** with arguments, evidence, and analysis
3. **Counter-argument** paragraph (address opposing views)
4. **Conclusion** that reinforces the thesis

Aim for 600-900 words. Use formal academic language."""
    return chat_single(prompt, "You are an expert essay writer. Write well-structured, academic-quality essays with proper formatting.")


def generate_mindmap(topic: str) -> str:
    """Generate a text-based mindmap structure."""
    prompt = f"""Create a comprehensive text-based mindmap for: {topic}

Use this tree format with box-drawing characters:
{topic}
├── Sub-topic 1
│   ├── Detail A
│   ├── Detail B
│   └── Detail C
├── Sub-topic 2
│   ├── Detail A
│   └── Detail B
└── Sub-topic 3
    ├── Detail A
    └── Detail B

Make it detailed with at least 3 main branches and 2-3 sub-items each."""
    return chat_single(prompt, "Create detailed text-based mindmaps using tree characters (├── └── │). Be comprehensive with at least 3 levels of depth.")


def create_presentation(topic: str) -> str:
    """Create presentation outline from notes."""
    prompt = f"""Create a professional slide-by-slide presentation outline for: {topic}

Format each slide as:
━━━ Slide 1: [Title] ━━━
📝 Content:
• Point 1
• Point 2
🖼️ Visual: [suggestion]

Include 10-12 slides with a clear flow: intro → content → conclusion."""
    return chat_single(prompt, "Create professional presentation outlines with clear slide structure.")


# ═══════════════════════════════════════════════════════════════
# SECTION 5: ENHANCED CODING TOOLS
# ═══════════════════════════════════════════════════════════════

def convert_code(code: str, from_lang: str, to_lang: str) -> str:
    """Convert code between programming languages."""
    prompt = f"""Convert this {from_lang} code to {to_lang}.
Provide the converted code in a markdown code block with {to_lang} specified.
Explain any significant differences or language-specific adaptations.

```{from_lang}
{code}
```"""
    result = chat_single(prompt, "You are an expert polyglot programmer. Convert code accurately between languages.")
    return f"🔄 *Code Conversion: {from_lang} → {to_lang}*\n\n{result}"


def coding_questions(topic: str) -> str:
    """Generate coding practice questions."""
    prompt = f"""Generate 5 coding practice questions about: {topic}

For each question provide:
- **Difficulty**: Easy/Medium/Hard
- **Problem**: Clear description
- **Example**: Input → Output
- **Hint**: A helpful hint
- **Topics Tested**: What concepts this tests

Order from easy to hard."""
    result = chat_single(prompt, "You are a coding interview coach. Generate practical, realistic coding problems with examples.")
    return f"💻 *Practice Questions: {topic}*\n\n{result}"


def coding_quiz(topic: str) -> str:
    """Generate coding quiz."""
    prompt = f"""Create a 10-question coding quiz about: {topic}
Format: MCQ with 4 options each.
Cover syntax, concepts, best practices, and common pitfalls.
Put the answer key at the very end."""
    result = chat_single(prompt, "Create coding quizzes that test real understanding, not just memorization.")
    return f"📝 *Coding Quiz: {topic}*\n\n{result}"


def code_improve(code: str) -> str:
    """Suggest code improvements."""
    prompt = f"""Analyze this code and suggest improvements in these areas:
1. **Performance** — optimizations
2. **Best Practices** — cleaner code
3. **Readability** — naming, structure
4. **Bug Prevention** — potential issues
5. **Security** — vulnerabilities

Provide the improved code in a code block, then explain changes.

```{code}```"""
    return chat_single(prompt, "You are a senior code reviewer. Suggest specific, actionable improvements with explanations.")


def detect_bugs(code: str) -> str:
    """Detect bugs and vulnerabilities."""
    prompt = f"""Thoroughly analyze this code for:
1. 🐛 **Bugs** — logic errors, edge cases, null references
2. 🔒 **Security Vulnerabilities** — injection, XSS, etc.
3. ⚡ **Performance Issues** — memory leaks, inefficiencies
4. 🧹 **Code Smells** — anti-patterns, bad practices

For each issue:
- Describe the problem
- Explain the impact
- Provide the fix

Code:
```{code}```"""
    return chat_single(prompt, "You are a security-focused senior code auditor. Find ALL bugs and vulnerabilities with fixes.")


# ═══════════════════════════════════════════════════════════════
# SECTION 6: RESEARCH & FACT-CHECKING
# ═══════════════════════════════════════════════════════════════

def fact_check(claim: str) -> str:
    """Fact-check a claim with confidence score."""
    # Search for evidence first
    search_results = ""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(f"fact check {claim}", max_results=5))
        search_results = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')[:150]}" for r in results])
    except Exception:
        pass

    prompt = f"""Fact-check this claim thoroughly: "{claim}"

Search results:
{search_results}

Provide:
1. **Verdict**: ✅ True / ⚠️ Mostly True / 🔶 Partially True / ⛔ Mostly False / ❌ False / ❓ Unverifiable
2. **Confidence Score**: XX%
3. **Evidence**: Supporting or contradicting facts
4. **Context**: Important background
5. **Sources**: Types of reliable sources"""
    result = chat_single(prompt, "You are a rigorous fact-checker. Always provide confidence scores and evidence-based analysis.")
    return f"🔍 *Fact Check*\n\n{result}"


def deep_research(topic: str) -> str:
    """Deep multi-step research on a topic."""
    # Search the web first
    search_results = ""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(topic, max_results=8))
        search_results = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')[:200]}" for r in results])
    except Exception:
        pass

    prompt = f"""Conduct a deep, multi-faceted research analysis on: {topic}

Web search results:
{search_results}

Provide comprehensive analysis:
1. **Overview** — thorough introduction
2. **Key Findings** — main discoveries and data
3. **Different Perspectives** — multiple viewpoints
4. **Data & Statistics** — numbers and evidence
5. **Historical Context** — background and evolution
6. **Current State** — latest developments
7. **Key Sources** — recommended further reading
8. **Conclusions** — summary of findings"""
    result = chat_single(prompt, "You are a thorough research analyst. Provide deep, well-sourced, multi-faceted analysis.")
    return f"🔬 *Deep Research: {topic}*\n\n{result}"


def verify_source(claim: str) -> str:
    """Verify source credibility."""
    prompt = f"""Evaluate the credibility of this claim/source: "{claim}"

Provide:
1. **Reliability Assessment**: High/Medium/Low
2. **Red Flags**: Any warning signs
3. **Cross-verification**: How to verify
4. **Recommended Sources**: Where to find reliable info on this topic"""
    return chat_single(prompt, "You are a media literacy expert. Evaluate source credibility objectively.")


def compare_answers(question: str) -> str:
    """Compare multiple answers to a question."""
    prompt = f"""Research and compare multiple perspectives/answers to: {question}

Provide:
1. **Answer 1**: [perspective/approach]
2. **Answer 2**: [different perspective/approach]
3. **Answer 3**: [another perspective/approach]
4. **Comparison**: Pros and cons of each
5. **Recommendation**: Which is best and when"""
    return chat_single(prompt, "Compare multiple approaches/perspectives objectively with pros and cons.")


# ═══════════════════════════════════════════════════════════════
# SECTION 7: AUTONOMOUS AGENT
# ═══════════════════════════════════════════════════════════════

def autonomous_agent(goal: str) -> str:
    """Autonomous agent: goal → plan → execute → report."""
    # Search for context first
    search_results = ""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(goal, max_results=5))
        search_results = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')[:150]}" for r in results])
    except Exception:
        pass

    prompt = f"""You are an autonomous AI agent. Given this goal, execute a thorough multi-step process.

Goal: {goal}

Context from web:
{search_results}

Follow this structure:

📋 **PHASE 1: PLANNING**
- Break down the goal into steps
- Identify what information is needed
- Plan the approach

⚡ **PHASE 2: EXECUTION**  
- Execute each step thoroughly
- Provide detailed information
- Address all aspects of the goal

📊 **PHASE 3: REPORT**
- Summary of what was accomplished
- Key findings and results
- Actionable recommendations
- Suggested next steps"""
    return chat_single(prompt, "You are an autonomous AI agent. Given a goal, plan it step by step, execute thoroughly, and provide a detailed report.")


# ═══════════════════════════════════════════════════════════════
# SECTION 8: VIDEO DOWNLOAD (YouTube, Instagram, Facebook)
# ═══════════════════════════════════════════════════════════════

def download_video(url: str) -> str:
    """Download video from URL. Returns file path or error string."""
    try:
        import yt_dlp

        output_path = tempfile.mktemp(suffix=".mp4", dir="/tmp")
        ydl_opts = {
            "format": "best[filesize<50M]/best",
            "outtmpl": output_path.replace(".mp4", "/%(title)s.%(ext)s"),
            "max_filesize": 50 * 1024 * 1024,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename) and os.path.getsize(filename) > 0:
                    return filename  # Success — return file path
                # Try to find the downloaded file
                for ext in ["mp4", "webm", "mkv"]:
                    candidate = output_path.replace(".mp4", f"/{info.get('title', 'video')}.{ext}")
                    if os.path.exists(candidate):
                        return candidate

        return "__ERROR__: Download completed but file not found."

    except ImportError:
        return "__ERROR__: yt-dlp not installed. This feature needs yt-dlp."
    except Exception as e:
        error_msg = str(e)
        if "video is unavailable" in error_msg.lower() or "private" in error_msg.lower():
            return "__ERROR__: Video is unavailable or private."
        if "age" in error_msg.lower():
            return "__ERROR__: Video is age-restricted."
        logger.error(f"Video download error: {e}")
        return f"__ERROR__: Download failed — {error_msg[:150]}"


def download_audio_from_video(url: str) -> str:
    """Download audio from video URL."""
    try:
        import yt_dlp

        output_path = tempfile.mktemp(suffix=".mp3", dir="/tmp")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path.replace(".mp3", "/%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                # Find the actual file (may have been converted to mp3)
                title = info.get("title", "audio")
                for ext in ["mp3", "m4a", "opus", "webm"]:
                    candidate = f"/tmp/{title}.{ext}"
                    if os.path.exists(candidate):
                        return candidate

        return "__ERROR__: Audio extraction completed but file not found."

    except ImportError:
        return "__ERROR__: yt-dlp or ffmpeg not available."
    except Exception as e:
        logger.error(f"Audio download error: {e}")
        return f"__ERROR__: {str(e)[:150]}"
