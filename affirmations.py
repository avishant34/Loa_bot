import random
from typing import List

# ========== HINDI / HINGLISH ==========
BASE_AFFIRMATIONS_HI = [
    "Main already woh sab feel kar raha/rahi hoon jo main chahta/chahti hoon. Yeh mera natural state hai.",
    "Mera subconscious mind ab nayi wealth, health aur love ki images accept kar raha hai.",
    "Main grateful hoon kyunki meri desires pehle se hi pure ho chuki hain.",
    "Main apne wish fulfilled ke feeling mein so raha/rahi hoon. Reality mere hisaab se shift ho rahi hai.",
    "Universe mere saath perfectly align hai. Jo bhi mere highest good ke liye hai, woh aa raha hai.",
    "Main abundance ka vortex mein hoon. Sirf wohi cheezein meri reality ban rahi hain jo main feel karta/karti hoon.",
    "Mere words powerful hain. Main sirf desired state ki baat karta/karti hoon.",
    "Main burning desire ke saath apne goal ko already achieve feel karta/karti hoon.",
    "Har din main apne future self ke closer aa raha/rahi hoon. Feeling is the secret.",
    "Main non-resistant hoon. Main allow karta/karti hoon ki acchi cheezein asani se aayein.",
]

GOAL_TEMPLATES_HI = [
    "Main already feel kar raha/rahi hoon ki {goal}. Yeh meri present reality hai.",
    "Main deeply grateful hoon kyunki {goal} — yeh already true hai.",
    "Mera subconscious is baat ko accept kar chuka hai: {goal}.",
    "Main {goal} ke feeling mein jeeta/jeeti hoon. Outer world ab match kar raha hai.",
    "Har cell of my body jaanta hai ki {goal}. Main allow karta/karti hoon.",
]

VISUALIZATION_PROMPTS_HI = [
    "Aankhein band karo. Abhi feel karo ki tumhara desire already pure ho chuka hai. Us moment ki khushi, shanti ya excitement ko abhi body mein feel karo. 1-2 minute usi feeling mein raho. Yeh Neville ka secret hai — Feeling is the Secret.",
    "Imagine karo ki tum apne future self se mil rahe ho jisne already goal achieve kar liya hai. Woh tumhe kya batata hai? Uske jaisa feel karo abhi.",
    "Ek scene banao jisme tumhara desire already true hai. Dekho, suno, chhuo. Phir us scene ke end pe so jao (SATS). Subah uthke bhi usi feeling ko yaad karo.",
    "Gratitude se shuru karo. 3 cheezein jo abhi hain unke liye shukriya. Phir apne desire ko already present maankar uska feeling badhao.",
    "Focus Wheel ki tarah: apne desire ke around positive statements socho jo honestly better feel karayein. Vibration raise karo.",
]

GRATITUDE_PROMPTS_HI = [
    "Aaj kis 3 cheezon ke liye tum genuinely grateful ho? Feeling ke saath likho.",
    "Kisne ya kis cheez ne aaj tumhara dil halka kiya? Uske liye shukriya.",
    "Apne body, mind ya kisi simple comfort ke liye deep gratitude feel karo.",
]

# ========== ENGLISH ==========
BASE_AFFIRMATIONS_EN = [
    "I already feel the reality of what I desire. This is my natural state.",
    "My subconscious mind now accepts new images of wealth, health and love.",
    "I am deeply grateful because my desires are already fulfilled.",
    "I fall asleep in the feeling of the wish fulfilled. Reality is shifting to match me.",
    "I am in complete alignment with the Universe. Only what is for my highest good is coming.",
    "I am in the vortex of abundance. Only that which I feel becomes my reality.",
    "My words are powerful. I speak only of the desired state.",
    "With burning desire I already feel my goal as accomplished.",
    "Every day I move closer to my future self. Feeling is the secret.",
    "I am non-resistant. I allow good things to come to me easily.",
]

GOAL_TEMPLATES_EN = [
    "I already feel that {goal}. This is my present reality.",
    "I am deeply grateful because {goal} — it is already true.",
    "My subconscious has accepted this: {goal}.",
    "I live in the feeling that {goal}. The outer world is catching up.",
    "Every cell of my body knows that {goal}. I allow it.",
]

VISUALIZATION_PROMPTS_EN = [
    "Close your eyes. Feel right now that your desire is already fulfilled. Let the joy, peace or excitement of that moment fill your body. Stay in that feeling for 1-2 minutes. This is Neville's secret — Feeling is the Secret.",
    "Imagine meeting your future self who has already achieved the goal. What do they tell you? Feel as they feel right now.",
    "Create a short scene in which your desire is already true. See, hear, touch it. Then fall asleep at the end of that scene (SATS). Carry the feeling when you wake.",
    "Start with gratitude. Feel thankful for 3 things you already have. Then assume your desire is present and amplify the feeling.",
    "Like a Focus Wheel: think of positive statements around your desire that honestly feel better. Raise your vibration.",
]

GRATITUDE_PROMPTS_EN = [
    "What 3 things are you genuinely grateful for today? Write them with feeling.",
    "Who or what lightened your heart today? Give thanks.",
    "Feel deep gratitude for your body, mind, or a simple comfort you enjoyed today.",
]


def _pick(lang: str, hi_list, en_list):
    return random.choice(en_list if lang == "en" else hi_list)


def generate_affirmation(goals: List[str] = None, category: str = None, lang: str = "hi") -> str:
    if goals and random.random() < 0.65:
        goal = random.choice(goals)
        templates = GOAL_TEMPLATES_EN if lang == "en" else GOAL_TEMPLATES_HI
        return random.choice(templates).format(goal=goal)
    return _pick(lang, BASE_AFFIRMATIONS_HI, BASE_AFFIRMATIONS_EN)


def get_visualization_prompt(lang: str = "hi") -> str:
    return _pick(lang, VISUALIZATION_PROMPTS_HI, VISUALIZATION_PROMPTS_EN)


def get_gratitude_prompt(lang: str = "hi") -> str:
    return _pick(lang, GRATITUDE_PROMPTS_HI, GRATITUDE_PROMPTS_EN)


def get_daily_message(goals: List[str], streak: int, name: str = None, lang: str = "hi") -> str:
    if lang == "en":
        greeting = f"Good morning {name}! ☀️" if name else "Good morning! ☀️"
        affirmation = generate_affirmation(goals, lang="en")
        streak_text = f"\n\n🔥 Current streak: *{streak} days*! Keep going." if streak > 0 else ""
        goals_text = ""
        if goals:
            goals_list = "\n".join([f"• {g}" for g in goals[:3]])
            goals_text = f"\n\n🎯 Your active goals:\n{goals_list}"
        return f"""{greeting}

✨ *Today's Affirmation:*
_{affirmation}_

{get_visualization_prompt('en')}
{goals_text}{streak_text}

Stay in the feeling of the wish fulfilled today.
You can share gratitude with /gratitude."""

    greeting = f"Good morning {name}! ☀️" if name else "Good morning! ☀️"
    affirmation = generate_affirmation(goals, lang="hi")
    streak_text = f"\n\n🔥 Aapki current streak: *{streak} days*! Keep going!" if streak > 0 else ""
    goals_text = ""
    if goals:
        goals_list = "\n".join([f"• {g}" for g in goals[:3]])
        goals_text = f"\n\n🎯 Aapke active goals:\n{goals_list}"
    return f"""{greeting}

✨ *Aaj ka Affirmation:*
_{affirmation}_

{get_visualization_prompt('hi')}
{goals_text}{streak_text}

Aaj wish fulfilled ke feeling mein raho.
/gratitude se aaj ki gratitude share kar sakte ho."""
