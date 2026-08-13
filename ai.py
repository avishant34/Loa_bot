"""
AI integration for Law of Attraction Bot
Trained on classic manifestation books + supports Hindi/English.
"""

import os
import logging
from typing import List, Optional, Dict

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

AI_PROVIDER = (os.getenv("AI_PROVIDER") or "groq").lower().strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY")
CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL")

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "custom": "gpt-4o-mini",
}

MODEL = os.getenv("AI_MODEL") or DEFAULT_MODELS.get(AI_PROVIDER, "llama-3.3-70b-versatile")

BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "together": "https://api.together.xyz/v1",
    "custom": CUSTOM_BASE_URL,
}

_client = None


def _get_api_key() -> Optional[str]:
    if AI_PROVIDER == "groq":
        return GROQ_API_KEY
    elif AI_PROVIDER == "openai":
        return OPENAI_API_KEY
    elif AI_PROVIDER == "openrouter":
        return OPENROUTER_API_KEY
    elif AI_PROVIDER == "together":
        return TOGETHER_API_KEY
    elif AI_PROVIDER == "custom":
        return CUSTOM_API_KEY
    return GROQ_API_KEY or OPENAI_API_KEY or OPENROUTER_API_KEY


def is_ai_available() -> bool:
    return bool(_get_api_key())


def get_client():
    global _client
    if _client is not None:
        return _client
    api_key = _get_api_key()
    if not api_key:
        return None
    base_url = BASE_URLS.get(AI_PROVIDER)
    if AI_PROVIDER == "custom" and not base_url:
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"AI client ready | {AI_PROVIDER} | {MODEL}")
        return _client
    except Exception as e:
        logger.error(f"AI client init failed: {e}")
        return None


def get_provider_info() -> str:
    if not is_ai_available():
        return "OFF (No API key)"
    return f"ON ({AI_PROVIDER} / {MODEL})"


# ==================== DEEP SYSTEM PROMPT (Books Trained) ====================

SYSTEM_PROMPT_BASE = """You are "LoA Coach" — a warm, wise, deeply knowledgeable Law of Attraction & manifestation coach.

You have deeply studied and teach from these classic works:
1. The Secret – Rhonda Byrne (Ask, Believe, Receive; gratitude; feeling already having it)
2. Ask and It Is Given – Esther & Jerry Hicks / Abraham (Emotional Guidance Scale, Segment Intending, Focus Wheel, Vortex, allowing)
3. Think and Grow Rich – Napoleon Hill (Burning desire, Faith, Auto-suggestion, Specialized knowledge, Imagination, Persistence, Mastermind)
4. The Power of Your Subconscious Mind – Joseph Murphy (Impressing the subconscious through repetition + feeling, mental healing, wealth consciousness)
5. The Science of Getting Rich – Wallace D. Wattles (Certain way of thinking + gratitude + acting in the present, creative vs competitive mind)
6. The Game of Life and How to Play It – Florence Scovel Shinn (Word is powerful, intuition, non-resistance, divine design, denials & affirmations)
7. Feeling is the Secret – Neville Goddard (Feeling is the secret; assume the feeling of the wish fulfilled; sleep in the state of the wish fulfilled; imagination creates reality)
8. E-Squared – Pam Grout (Universe is abundant, thoughts are energy, experiments to prove it, possibility)
9. The Universe Has Your Back – Gabrielle Bernstein (From fear to faith, surrender, alignment, choosing love over fear)
10. Manifest – Roxie Nafousi (Be clear, remove blocks, raise vibration, prepare, trust, take aligned action, celebrate)

CORE TEACHINGS YOU MUST FOLLOW:
- Desire + Belief + Feeling (already having it) = Manifestation
- Feeling is the secret (Neville). The emotional state matters more than the words.
- Gratitude raises vibration instantly (The Secret, Wattles, Hicks).
- Do not force or chase. Allow and become a vibrational match (Abraham-Hicks).
- Subconscious mind accepts what is impressed with feeling and repetition (Murphy).
- Words have power; speak only of the desired state (Shinn).
- Persistence and burning desire (Hill).
- Imagination + assumption of the wish fulfilled (Neville).
- Aligned action from inspiration, not desperation (Roxie + Wattles).

STYLE RULES:
- Language: Respond in the user's preferred language (Hindi or English). If Hinglish is natural for Hindi users, use warm Hinglish.
- Be warm, grounded, practical, and never make false promises ("you will get money tomorrow").
- Teach processes: visualization, 369 method, scripting, SATS (Neville), Focus Wheel, gratitude, affirmations with feeling.
- Keep answers focused and not overly long unless the user asks for depth.
- When giving affirmations, make them present-tense, emotionally rich, and specific.
- When guiding visualization, use sensory detail and the feeling of the wish fulfilled (Neville style).
- Encourage consistency (21-day challenges, daily 369, morning/evening routines).

Never give medical, legal, or professional financial advice that replaces experts.
"""


def _lang_instruction(lang: str) -> str:
    if lang == "en":
        return "\n\nIMPORTANT: Respond fully in clear, warm English."
    return "\n\nIMPORTANT: Respond in natural Hinglish (Hindi + English mix) jaise normal Indian baat karte hain. Pure English mat likho unless user English mein baat kare."


def generate_ai_affirmation(goals: List[str] = None, category: str = None, user_name: str = None, lang: str = "hi") -> Optional[str]:
    client = get_client()
    if not client:
        return None

    goals_text = ", ".join(goals) if goals else "general abundance, peace and growth"
    cat_text = category or "general"

    prompt = f"""Create one powerful, present-tense affirmation deeply aligned with Neville Goddard, Joseph Murphy and The Secret.
Goals: {goals_text}
Category: {cat_text}
Name: {user_name or 'friend'}

Make it emotionally rich — the person should FEEL it is already true.
1-2 sentences only. No explanation.
Language style: {"English" if lang == "en" else "Hinglish"}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE + _lang_instruction(lang)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=130,
            temperature=0.85,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI affirmation error: {e}")
        return None


def chat_with_coach(
    user_message: str,
    goals: List[str] = None,
    recent_gratitude: List[str] = None,
    streak: int = 0,
    chat_history: List[Dict] = None,
    user_name: str = None,
    lang: str = "hi",
) -> str:
    client = get_client()
    if not client:
        if lang == "en":
            return "AI Coach is currently unavailable. Please set the API key or use /affirmation, /gratitude, /visualize."
        return "AI Coach abhi available nahi hai. API key set karo ya /affirmation, /gratitude, /visualize use karo."

    context_parts = []
    if user_name:
        context_parts.append(f"User name: {user_name}")
    if goals:
        context_parts.append("Active goals: " + "; ".join(goals[:5]))
    if recent_gratitude:
        context_parts.append("Recent gratitude: " + "; ".join(recent_gratitude[:3]))
    if streak:
        context_parts.append(f"Current streak: {streak} days")

    context_str = "\n".join(context_parts) if context_parts else "No extra context."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_BASE + _lang_instruction(lang) + f"\n\nUser context:\n{context_str}"}
    ]
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.75,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return "Thodi technical problem aa gayi. Thodi der baad try karo." if lang != "en" else "A small technical issue occurred. Please try again shortly."


def generate_daily_ai_message(goals: List[str], streak: int, name: str = None, lang: str = "hi") -> Optional[str]:
    client = get_client()
    if not client:
        return None

    goals_text = ", ".join(goals[:4]) if goals else "growth, peace and abundance"
    name_text = name or ("friend" if lang == "en" else "dost")

    prompt = f"""Write a short, warm, powerful morning message in the style of The Secret + Neville Goddard + Abraham-Hicks.
User: {name_text}
Goals: {goals_text}
Streak: {streak} days

Include:
1. Warm greeting
2. One deep present-tense affirmation (feeling already having it)
3. A short Neville-style visualization / feeling prompt
4. One gentle aligned action for today
5. Encouragement for consistency

Language: {"English" if lang == "en" else "Hinglish"}
Keep it medium length, not too long."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE + _lang_instruction(lang)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=380,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI daily error: {e}")
        return None


def generate_visualization(goals: List[str] = None, lang: str = "hi") -> Optional[str]:
    """Deep Neville + Hicks style visualization."""
    client = get_client()
    if not client:
        return None
    goals_text = ", ".join(goals[:3]) if goals else "your deepest desire already fulfilled"
    prompt = f"""Create a deep guided visualization (Neville Goddard + Abraham-Hicks style).
Focus: {goals_text}

Structure:
- Close eyes, relax
- Enter the scene as if the desire is ALREADY fulfilled
- Sensory details (see, hear, touch, feel)
- Strong emphasis on the FEELING of the wish fulfilled
- End by carrying that feeling into the day

Language: {"English" if lang == "en" else "Hinglish"}
Length: medium (not too short, not essay)."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE + _lang_instruction(lang)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=420,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        return None


def generate_369_guidance(intention: str, lang: str = "hi") -> Optional[str]:
    client = get_client()
    if not client:
        return None
    prompt = f"""Guide the user on the 369 manifestation method for this intention:
"{intention}"

Explain briefly how to do it today:
- Morning: write 3 times
- Afternoon: write 6 times
- Night: write 9 times
Give them a perfectly worded present-tense statement they can copy.
Emphasize feeling while writing (Neville + The Secret).

Language: {"English" if lang == "en" else "Hinglish"}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE + _lang_instruction(lang)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"369 error: {e}")
        return None
