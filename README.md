# 🤖📸 AI Instagram Publisher

A Python-based application that automatically generates visually engaging content using AI (images + captions) and publishes it to Instagram — all on autopilot.

---

## 🚀 Features

- ✨ **AI Image Generation** — Uses OpenAI DALL·E (or Stable Diffusion) to create beautiful visuals based on dynamic prompts.
- 🧠 **AI Caption Writing** — GPT-based generation of engaging, hashtag-rich captions.
- 👁️ **(Optional) Human Review** — Content can be approved via Telegram or web before posting.
- 📅 **Scheduling** — Automatically generates and publishes posts at configured intervals.
- 📲 **Instagram Integration** — Uses Graph API or third-party tools to automate posting.

---

## 📂 Project Structure

```bash
instagram_ai_publisher/
├── main.py                      # Main orchestrator script
├── config.py                   # App settings, .env loader
├── scheduler.py                # Cron-like scheduling (optional)
├── generator/
│   ├── image_generator.py      # AI-based image creation
│   └── caption_generator.py    # GPT caption generation
├── publisher/
│   └── instagram_publisher.py  # Post to Instagram
├── reviewer/
│   └── telegram_bot.py         # Optional content approval
├── utils/
│   ├── logger.py               # Centralized logging
│   └── helpers.py              # Utility functions
├── requirements.txt
└── .env                        # API keys and environment vars