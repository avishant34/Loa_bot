import random
from typing import List, Optional

# Base affirmations in Hindi + English mix (Hinglish friendly)
BASE_AFFIRMATIONS = [
    "Main apne goals ki taraf confidently badh raha/rahi hoon. Universe meri madad kar raha hai.",
    "Main grateful hoon har chhoti-badi cheez ke liye jo mere paas hai.",
    "Mere thoughts powerful hain. Main positive energy attract karta/karti hoon.",
    "Main deserve karta/karti hoon abundance, love aur success.",
    "Har din main better version of myself ban raha/rahi hoon.",
    "Main open hoon naye opportunities ke liye. Jo bhi best hai, woh aa raha hai.",
    "Mere dreams real ho rahe hain. Main unhe already feel kar raha/rahi hoon.",
    "Main trust karta/karti hoon the process. Sab kuch perfect timing pe ho raha hai.",
    "Main apni energy protect karta/karti hoon aur sirf positive logon ko allow karta/karti hoon.",
    "Main abundant hoon. Paisa, health aur happiness naturally flow karte hain mere life mein.",
    "Main love aur respect deserve karta/karti hoon — pehle khud se, phir dusron se.",
    "Mera mind calm hai, mera heart open hai, aur mera future bright hai.",
    "Main har obstacle ko opportunity mein badal deta/deti hoon.",
    "Universe mere saath hai. Main aligned hoon apne highest good ke saath.",
    "Main already woh person hoon jo main banna chahta/chahti hoon.",
]

GOAL_TEMPLATES = [
    "Main confidently manifest kar raha/rahi hoon: {goal}. Yeh already meri reality ban chuka hai.",
    "Main grateful hoon ki {goal} meri life ka hissa ban gaya hai.",
    "Har din main {goal} ke closer aa raha/rahi hoon. Energy match ho rahi hai.",
    "Main deserve karta/karti hoon {goal}. Aur main isse receive karne ke liye ready hoon.",
    "My focus is clear: {goal}. Main iske liye inspired action le raha/rahi hoon.",
]

VISUALIZATION_PROMPTS = [
    "Aankhein band karo. Imagine karo ki tumhara goal already pure ho chuka hai. Us moment ka feeling kaisa hai? Khushi, shanti, excitement? Us feeling ko abhi feel karo 1 minute ke liye.",
    "Apne ideal day ko visualize karo. Subah uthte hi kya feel hota hai? Din kaise guzarta hai? Log tumhe kaise dekhte hain? Detail mein socho.",
    "Ek saal baad khud ko dekho. Tumhara goal achieve ho chuka hai. Tum kahan ho? Kya kar rahe ho? Kaun log tumhare saath hain? Us future self se ek message lo.",
    "Apne desire ko ek bright light ki tarah imagine karo jo tumhari taraf aa raha hai. Us light ko receive karo aur body mein feel karo.",
    "Gratitude se shuru karo. 3 cheezein socho jo abhi tumhare paas hain. Phir apne goal ko already present ki tarah feel karo.",
]

GRATITUDE_PROMPTS = [
    "Aaj kis 3 cheezon ke liye tum genuinely grateful ho? Chhoti se chhoti cheez bhi likho.",
    "Kisne aaj tumhari madad ki ya smile diya? Unke liye gratitude feel karo.",
    "Apne body, health ya mind ki kisi ek baat ke liye shukriya ada karo.",
    "Nature, technology ya kisi simple comfort ke liye grateful feel karo jo aaj use kiya.",
]

CATEGORY_AFFIRMATIONS = {
    "money": [
        "Paisa easily aur frequently mere paas aata hai.",
        "Main money magnet hoon. Abundance mera natural state hai.",
        "Main financial freedom ke liye ready hoon aur usse attract kar raha/rahi hoon.",
    ],
    "love": [
        "Main deep, healthy aur respectful love deserve karta/karti hoon.",
        "Mera heart open hai. Right person meri taraf aa raha hai.",
        "Main pehle khud se pyaar karta/karti hoon, isliye dusre bhi meri value karte hain.",
    ],
    "health": [
        "Mera body strong, healthy aur energetic hai.",
        "Main apne body ko love aur care deta/deti hoon. Healing naturally ho rahi hai.",
        "Har cell of my body vibrates with health and vitality.",
    ],
    "career": [
        "Main apne dream career mein success attract kar raha/rahi hoon.",
        "Opportunities meri taraf aa rahi hain. Main unhe recognize karta/karti hoon.",
        "Main valuable hoon. Meri skills aur energy ko market appreciate karta hai.",
    ],
    "general": BASE_AFFIRMATIONS,
}


def generate_affirmation(goals: List[str] = None, category: str = None) -> str:
    """Generate a personalized affirmation."""
    if goals and random.random() < 0.6:
        goal = random.choice(goals)
        template = random.choice(GOAL_TEMPLATES)
        return template.format(goal=goal)

    if category and category in CATEGORY_AFFIRMATIONS:
        return random.choice(CATEGORY_AFFIRMATIONS[category])

    return random.choice(BASE_AFFIRMATIONS)


def get_visualization_prompt() -> str:
    return random.choice(VISUALIZATION_PROMPTS)


def get_gratitude_prompt() -> str:
    return random.choice(GRATITUDE_PROMPTS)


def get_daily_message(goals: List[str], streak: int, name: str = None) -> str:
    """Create a rich daily morning message."""
    greeting = f"Good morning {name}! ☀️" if name else "Good morning! ☀️"
    affirmation = generate_affirmation(goals)

    streak_text = ""
    if streak > 0:
        streak_text = f"\n\n🔥 Aapki current streak: *{streak} days*! Keep going!"

    goals_text = ""
    if goals:
        goals_list = "\n".join([f"• {g}" for g in goals[:3]])
        goals_text = f"\n\n🎯 Aapke active goals:\n{goals_list}"

    message = f"""{greeting}

✨ *Aaj ka Affirmation:*
_{affirmation}_

{get_visualization_prompt()}
{goals_text}{streak_text}

Aaj bhi grateful rehna aur positive energy maintain karna.
/gratitude likh ke aaj ki 3 cheezein share kar sakte ho.
"""
    return message.strip()
