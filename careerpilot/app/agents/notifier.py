import httpx

from .. import config
from ..models import Alert, Match


def format_alert(m: Match) -> str:
    j = m.job
    keys = "\n".join(f"✓ {k}" for k in m.matched[:5])
    return (f"🔥 NEW {m.profile.role.upper()} MATCH\nScore: {m.final_score}%\n\n{j.title} - {j.company}\n"
            f"{j.location}\n{j.job_type}\n\nKey Match:\n{keys}\n\nApply:\n{j.url}")


def send_telegram(text: str) -> tuple[bool, str]:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        return False, "Telegram not configured"
    try:
        r = httpx.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                       json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text}, timeout=15)
        r.raise_for_status()
        return True, "sent"
    except Exception as e:
        return False, f"{type(e).__name__}"


def notify(m: Match, db) -> bool:
    text = format_alert(m)
    ok, info = send_telegram(text)
    db.add(Alert(match_id=m.id, channel="telegram", ok=ok, message=text + f"\n[{info}]"))
    return ok
