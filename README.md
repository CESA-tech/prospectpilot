# ProspectPilot

AI-powered B2B outreach automation — researches companies, writes personalized emails, sends them, and follows up automatically.

---

## What It Does

Most outreach tools send the same template to everyone. ProspectPilot researches each company before writing the email — pain points, recent activity, product focus — and generates a message that reads like it was written by a human who did their homework.

**Full pipeline:**

1. **Research** — Tavily web search + Claude AI analyzes the target company
2. **Enrich** — Hunter.io finds decision-maker contact info
3. **Draft** — Claude writes a personalized cold email based on research
4. **Review** — Human approves, edits, or regenerates with a different style
5. **Send** — SendGrid delivers the email from your domain
6. **Follow-up** — Gmail API checks for replies; sends follow-up at day 3 and day 7 if no response
7. **Schedule** — APScheduler runs the follow-up check daily at 09:00 automatically

---

## Architecture

```
User Input (company name)
        │
        ▼
┌───────────────────┐
│  Research Agent   │  ← Claude + Tavily (web search)
│  (LangGraph node) │
└────────┬──────────┘
         │ company profile
         ▼
┌───────────────────┐
│  Enrichment Tool  │  ← Hunter.io (find contacts)
└────────┬──────────┘
         │ contact info
         ▼
┌───────────────────┐
│   Draft Agent     │  ← Claude (personalized email)
│  (style system)   │
└────────┬──────────┘
         │ draft email
         ▼
┌───────────────────┐
│  Human Review     │  ← Streamlit UI / Terminal
│  (approve/edit)   │
└────────┬──────────┘
         │ approved
         ▼
┌───────────────────┐     ┌─────────────────────┐
│   Email Sender    │     │   Reply Detector     │
│   (SendGrid)      │────▶│   (Gmail API)        │
└───────────────────┘     └──────────┬───────────┘
                                     │ no reply after 3/7 days
                                     ▼
                          ┌─────────────────────┐
                          │  Follow-up Agent     │
                          │  (APScheduler)       │
                          └─────────────────────┘
```

---

## Features

- **Personalized research** — every email is based on real company data, not a template
- **Style system** — 5 built-in styles (pain point, momentum, short, formal, curious) + create and save custom styles
- **Human-in-the-loop** — review and edit every email before it sends
- **Automatic follow-ups** — day 3 and day 7 follow-ups with reply detection
- **Batch processing** — upload a CSV, process multiple companies at once
- **Lead management** — track status (draft → sent → replied) with full history
- **Streamlit UI** — browser-based interface, no terminal required
- **Daily scheduler** — runs follow-up checks automatically every morning

---

## Tech Stack

| Layer | Tool |
|-------|------|
| AI / LLM | Claude (claude-sonnet-4-6) |
| Agent framework | LangGraph |
| Web research | Tavily |
| Contact enrichment | Hunter.io |
| Email delivery | SendGrid |
| Reply detection | Gmail API |
| Scheduling | APScheduler |
| Database | SQLite (SQLAlchemy) |
| UI | Streamlit |

---

## Project Structure

```
prospectpilot/
├── app.py                    # Streamlit UI
├── main.py                   # Terminal menu
├── config/
│   └── outreach_styles.json  # Email styles
├── data/
│   └── leads.csv             # Batch input (example)
├── docs/
│   ├── setup-guide.md        # Full setup guide (developer)
│   └── client-guide.md       # Client setup guide
├── src/
│   ├── agents/
│   │   ├── research_agent.py # Company research
│   │   └── draft_agent.py    # Email generation
│   ├── db/
│   │   ├── models.py         # Lead model
│   │   ├── crud.py           # DB operations
│   │   └── viewer.py         # Terminal lead viewer
│   ├── pipeline/
│   │   └── graph.py          # LangGraph pipeline
│   ├── tools/
│   │   ├── enrichment.py     # Hunter.io
│   │   ├── email_sender.py   # SendGrid
│   │   ├── reply_detector.py # Gmail API
│   │   └── follow_up.py      # Follow-up logic
│   └── scheduler.py          # APScheduler
└── .env.example              # Environment variables template
```

---

## Setup

Requires Python 3.10+, API keys for Anthropic, Tavily, Hunter.io, and SendGrid, plus a domain for email sending.

Full setup instructions: [`docs/setup-guide.md`](docs/setup-guide.md)

Quick start:

```powershell
git clone https://github.com/CESA-tech/prospectpilot.git
cd prospectpilot
python -m venv venv
.\venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env   # fill in your API keys
.\venv\Scripts\streamlit run app.py
```

---

## Usage

**Streamlit UI (recommended):**
```powershell
.\venv\Scripts\streamlit run app.py
```

**Terminal:**
```powershell
.\venv\Scripts\python main.py
```

**Scheduler (daily follow-ups):**
```powershell
.\venv\Scripts\python src\scheduler.py
```

---

## Demo

[![ProspectPilot Demo](https://img.shields.io/badge/Watch%20Demo-Loom-blue)](https://www.loom.com/share/46979ea855814e9797d9f963d3a6f68b)

Full pipeline walkthrough: research → contact → draft → approve → send.

---

*Built with Claude + LangGraph for AI-powered outreach automation.*
