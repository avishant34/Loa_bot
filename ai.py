"""
AI integration for Law of Attraction Bot
Supports multiple providers (Free + Paid) using OpenAI-compatible API.

Recommended free: Groq
Later paid: OpenAI
"""

import os
import logging
from typing import List, Optional, Dict

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ==================== PROVIDER CONFIG ====================
# .env se values aati hain

# Provider: "groq" | "openai" | "openrouter" | "together" | "custom"
AI_PROVIDER = (os.getenv("AI_PROVIDER") or "groq").lower().strip()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY")
CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL")

# Models (defaults)
DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",       # Fast + good quality (free tier)
    "openai": "gpt-4o-mini",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "custom": "gpt-4o-mini",
}

MODEL = os.getenv("AI_MODEL") or DEFAULT_MODELS.get(AI_PROVIDER, "llama-3.3-70b-versatile")

# Base URLs for OpenAI-compatible providers
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
    # fallback
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
        logger.error("CUSTOM_BASE_URL not set")
        return None

    try:
        from openai import OpenAI
        _client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"AI client ready | Provider: {AI_PROVIDER} | Model: {MODEL}")
        return _client
    except Exception as e:
        logger.error(f"Failed to init AI client: {e}")
        return None


def get_provider_info() -> str:
    """Human readable status"""
    if not is_ai_available():
        return "OFF (No API key)"
    return f"ON ({AI_PROVIDER} / {MODEL})"


# ==================== SYSTEM PROMPT ====================

SYSTEM_PROMPT = """Tum ek warm, supportive aur wise Law of Attraction / Manifestation coach ho.
Tumhara naam "LoA Coach" hai.

Rules:
- Hinglish mein baat karo (Hindi + English mix) jaise normal Indian log baat karte hain.
- Positive, empowering aur grounded raho. Kabhi bhi false promises mat do jaise "kal tak paisa aa jayega".
- Focus rakho: mindset, gratitude, clear intentions, inspired action, consistency.
- User ke goals, feelings aur blocks ko samjho.
- Short aur practical answers do (zyada lamba mat likho unless user detail maange).
- Kabhi kabhi powerful affirmation suggest karo.
- Agar user negative feel kar raha ho to empathetically suno phir gently reframing karo.
- Spiritual + practical balance rakho.
- Kabhi bhi medical, legal ya financial advice mat do jo professional ki jagah le.
"""


# ==================== AI FUNCTIONS ====================

def generate_ai_affirmation(goals: List[str] = None, category: str = None, user_name: str = None) -> Optional[str]:
    """Generate a personalized affirmation."""
    client = get_client()
    if not client:
        return None

    goals_text = ", ".join(goals) if goals else "general abundance and growth"
    cat_text = category or "general"

    prompt = f"""User ke liye ek powerful, present-tense affirmation banao.
Goals: {goals_text}
Category focus: {cat_text}
Name: {user_name or 'dost'}

Sirf affirmation likho (1-2 sentences). Hinglish ya pure Hindi/English — natural lage.
Koi extra explanation mat do."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=120,
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
) -> str:
    """Free-form chat with the LoA coach."""
    client = get_client()
    if not client:
        return (
            "AI Coach abhi available nahi hai.\n\n"
            "API key set nahi hai. `.env` file check karo.\n"
            "Tab tak /affirmation, /gratitude, /visualize use karo."
        )

    context_parts = []
    if user_name:
        context_parts.append(f"User ka naam: {user_name}")
    if goals:
        context_parts.append("Active goals: " + "; ".join(goals[:5]))
    if recent_gratitude:
        context_parts.append("Recent gratitude: " + "; ".join(recent_gratitude[:3]))
    if streak:
        context_parts.append(f"Current streak: {streak} days")

    context_str = "\n".join(context_parts) if context_parts else "Koi extra context nahi."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nCurrent user context:\n{context_str}"}
    ]

    if chat_history:
        for msg in chat_history[-6:]:
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=450,
            temperature=0.75,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return "Thodi technical problem aa gayi. Thodi der baad try karo, ya /affirmation use karo."


def generate_daily_ai_message(goals: List[str], streak: int, name: str = None) -> Optional[str]:
    """Generate a rich personalized daily morning message."""
    client = get_client()
    if not client:
        return None

    goals_text = ", ".join(goals[:4]) if goals else "general growth aur abundance"
    name_text = name or "dost"

    prompt = f"""Ek short, warm, motivating morning message likho Law of Attraction style mein.
User: {name_text}
Goals: {goals_text}
Streak: {streak} days

Message mein ho:
1. Warm greeting
2. Ek powerful personalized affirmation (goals se related)
3. Ek chhota visualization / feeling prompt
4. Streak motivate karne wali line (agar streak > 0)
5. Aaj ke liye ek simple action suggestion

Hinglish mein, natural tone. Length medium rakho (not too long)."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI daily message error: {e}")
        return None
