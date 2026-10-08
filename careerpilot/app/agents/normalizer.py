import html
import re


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _type(raw: str, text: str) -> str:
    t = f"{raw} {text}".lower()
    if "part-time" in t or "part_time" in t or "part time" in t:
        return "Part-time"
    if "contract" in t:
        return "Contract"
    return "Full-time"


def normalize(raw: dict) -> dict | None:
    title, company = _clean(raw.get("title")), _clean(raw.get("company"))
    if not title or not company:
        return None
    desc = _clean(raw.get("description"))
    return {
        "title": title,
        "company": company,
        "location": _clean(raw.get("location")) or "Ireland",
        "job_type": _type(raw.get("job_type") or "", desc),
        "description": desc[:6000],
        "url": raw.get("url") or "",
        "source": raw.get("source") or "Unknown",
        "posted_at": str(raw.get("posted_at") or "")[:10],
    }
