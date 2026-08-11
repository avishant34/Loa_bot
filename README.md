# 🌟 Law of Attraction Bot + AI Coach (Telegram)

Complete **Law of Attraction / Manifestation Bot** with **OpenAI-powered AI Coach**.

Users can:
- Get personalized affirmations
- Set & track goals
- Practice gratitude
- Do visualizations
- Build streaks
- **Freely chat with an AI Manifestation Coach** in Hinglish

---

## Features

| Feature | Description |
|---------|-------------|
| ✨ Affirmations | AI-generated (agar key ho) warna local smart templates |
| 🎯 Goals | Present-tense goals + categories (Money, Love, Health, Career) |
| 🙏 Gratitude | Daily gratitude journal + streak |
| 🧘 Visualization | Guided prompts |
| 🔥 Streak | Consistency tracker |
| 💬 **AI Chat** | Free conversation with LoA Coach (OpenAI) |
| 🔔 Daily Messages | Morning affirmation + motivation (AI enhanced) |
| 🇮🇳 Hinglish | Natural Indian style communication |

---

## Setup

### 1. Telegram Bot Token
1. Telegram → **@BotFather**
2. `/newbot` → naam aur username do
3. Token copy karo

### 2. OpenAI API Key (recommended)
1. https://platform.openai.com/api-keys pe jao
2. Naya key banao
3. Copy karo (`sk-...`)

> Bina OpenAI key ke bhi bot chalega (local affirmations), lekin **Chat Coach** aur smart affirmations nahi aayenge.

### 3. Install
```bash
cd loa_bot
pip install -r requirements.txt
```

### 4. Run
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
export OPENAI_API_KEY="sk-proj-..."          # optional but recommended
# optional: export OPENAI_MODEL="gpt-4o-mini"  # default already good & cheap

python bot.py
```

Windows PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN="your-token"
$env:OPENAI_API_KEY="sk-..."
python bot.py
```

### 5. Test
Telegram pe bot kholo → `/start` → try `/chat` ya seedha message bhejo.

---

## Commands

| Command | Kaam |
|---------|------|
| `/start` | Welcome + menu |
| `/affirmation` | Personalized affirmation (AI + local) |
| `/setgoal` | Naya goal add karo |
| `/mygoals` | Goals dekho / remove |
| `/gratitude` | Gratitude entry |
| `/visualize` | Visualization prompt |
| `/streak` | Streak dekho |
| `/chat` | AI Coach se baat shuru karo |
| `/stopchat` | Chat mode band karo |
| `/clear` | Chat history clear |
| `/daily` | Daily morning messages on/off |
| `/settings` | Settings |
| `/help` | Help |

**Pro tip:** Chat mode on hone ke baad seedha apna message type karo. AI Coach reply karega.

---

## How AI Chat works

- User ke active goals + recent gratitude + streak context mein jaate hain
- Last few messages yaad rehte hain (short memory)
- Hinglish mein warm, grounded, practical guidance
- False promises nahi karta (“kal tak millionaire”) — mindset + action pe focus

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | BotFather se mila token |
| `OPENAI_API_KEY` | No* | OpenAI key (*Chat + smart affirmations ke liye chahiye) |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` (sasta + accha) |

---

## Folder Structure
```
loa_bot/
├── bot.py              # Main Telegram bot
├── ai.py               # OpenAI integration (chat + affirmations)
├── database.py         # SQLite
├── affirmations.py     # Local fallback content
├── requirements.txt
├── README.md
└── loa_bot.db          # Auto-created
```

---

## Production Tips
- 24/7 ke liye Railway / Render / VPS / Fly.io use karo
- Token & OpenAI key environment variables mein rakho (code mein mat likho)
- Cost control: `gpt-4o-mini` use karo (bahut sasta)
- Rate limit / abuse control baad mein add kar sakte ho
- Chat history abhi in-memory hai — production mein Redis ya DB better hai

---

Banaya gaya hai with ❤️ for conscious manifestation.
Koi improvement chahiye to batao!
