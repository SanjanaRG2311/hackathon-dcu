# CareerPilot

Autonomous multi-profile AI job hunter. Python only: FastAPI, SQLAlchemy/SQLite, APScheduler, Jinja2 + Tailwind + HTMX.

Pipeline: Discover -> Normalize -> Deduplicate -> AI Match -> Telegram alert -> optional application draft (approval required, nothing is ever sent automatically).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 and click **Run Demo Scan**. Three sample profiles (PMO Dublin, Project Manager Cork, Scrum Master Limerick) are seeded on first start.

## Configuration (.env)

| Variable | Purpose |
|---|---|
| ANTHROPIC_API_KEY | LLM matching and CV/cover letter drafts. Without it a keyword/title heuristic is used. |
| ANTHROPIC_MODEL | Defaults to claude-sonnet-4-6 |
| TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID | Alerts. Create a bot with @BotFather, message it, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to read your chat id. |
| ADZUNA_APP_ID, ADZUNA_APP_KEY, REED_API_KEY | Live job sources. Without them the scheduler runs on the demo dataset. |
| SCAN_MINUTES | Scheduled scan interval, default 15 |

## Pages

- `/` dashboard: stats, live pipeline, ranked matches, applications Kanban
- `/profiles` profile CRUD with resume upload
- `/alerts` alert history and test notification
- `/review/{id}` tailored CV summary and cover letter, approve to move to the Approved column

## Notes

- Matches at or above a profile's minimum score trigger a Telegram alert; matches above 90 also get a drafted application.
- Duplicates are detected by company + location + fuzzy title and merged into one job with all source links.
- LinkedIn, Indeed, IrishJobs and Jobs.ie block scraping, so live discovery uses the Adzuna and Reed APIs; those boards appear in demo data.
